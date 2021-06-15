import json
from collections import defaultdict
from typing import List, Union, Dict, Tuple

from django.db import IntegrityError
from django.db.models import QuerySet

from audience_toolkits import settings
from core.audience.models.base_model import SuperviseModel, RuleBaseModel
from core.audience.models.classic.term_weight_model import TermWeightModel
from core.dao.input_example import Features, InputExample
from core.helpers.model_helpers import get_model_class
from labeling_jobs.models import Document, LabelingJob, Label
from labeling_jobs.tasks import create_documents, read_csv_file
from modeling_jobs.models import ModelingJob, UploadModelJob

TERM_WEIGHT_FIELDS_MAPPING = {
    'content': '字詞',
    'label': '標籤',
    'score': '分數',
}


def import_model_data_task(upload_job: UploadModelJob):
    upload_job.job_status = UploadModelJob.JobStatus.PROCESSING
    upload_job.save()
    try:
        file = upload_job.file
        print(upload_job.modeling_job.model_name)
        if upload_job.modeling_job.model_name in {"TERM_WEIGHT_MODEL"}:
            import_term_weights(file, upload_job.modeling_job, update_labels=True,
                                required_fields=TERM_WEIGHT_FIELDS_MAPPING)
        else:
            raise ValueError(f'Unknown or unsupported model {upload_job.modeling_job.model_name}.')
        upload_job.job_status = UploadModelJob.JobStatus.DONE
    except Exception as e:
        print(e)
        upload_job.job_status = UploadModelJob.JobStatus.ERROR
    finally:
        upload_job.save()


def import_term_weights(file, job: ModelingJob, required_fields=None, update_labels=False):
    if not required_fields:
        required_fields = TERM_WEIGHT_FIELDS_MAPPING
    label_term_weight: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    csv_rows = read_csv_file(file, required_fields)

    for index, row in enumerate(csv_rows):
        data = defaultdict(str)
        for _field in required_fields.keys():
            # 判斷欄位是否有出現在可使用的欄位名稱列表中
            field_data = row.get(_field, None) or row.get(required_fields.get(_field), None)
            if _field == 'score':
                field_data = field_data if field_data else 1
            data[_field] = field_data
        label_str: str = data.get('label', None)
        content = data.get('content', None)
        score = data.get('score', 1)
        label_term_weight[label_str].append((content, score))
    create_term_weights(job=job, label_term_weight=label_term_weight)
    pass


def train_model_task(job: ModelingJob):
    job.job_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        model_path = f"{job.id}_{job.name}"
        model = get_model(job, model_path, for_training=True, na_tag='一般')
        if isinstance(model, SuperviseModel):
            train_set = job.jobRef.get_train_set()
            contents, y_true = get_examples_and_labels(train_set)
            job.model_path = model.fit(examples=contents, y_true=y_true)

            if isinstance(model, TermWeightModel):
                create_term_weights(job, model.label_term_weights)
            # get train set report
            eval_dataset(model=model, dataset_type=Document.TypeChoices.TRAIN, dataset=train_set, job=job)
        elif isinstance(model, RuleBaseModel):
            raise ValueError(f"{model.__class__.__name__} is not trainable.")

        # get dev set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.DEV, dataset=job.jobRef.get_dev_set(), job=job)

        # get test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.TEST, dataset=job.jobRef.get_test_set(), job=job)

        job.job_status = ModelingJob.JobStatus.DONE
        job.save()
        print('training done')

    except Exception as e:
        print(e)
        job.error_message = e
        job.job_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def testing_model_via_ext_data_task(uploaded_file, job: ModelingJob, remove_old_data=True):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        create_ext_data(uploaded_file=uploaded_file, job=job.jobRef, remove_old_data=remove_old_data)
        print(job.model_name, job.model_path, job.is_multi_label)
        model = get_model(job)
        if isinstance(model, TermWeightModel):
            model.load(get_term_weights(job))
        # get ext test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.EXT_TEST, dataset=job.jobRef.get_ext_test_set(),
                     job=job)
        job.ext_test_status = ModelingJob.JobStatus.DONE
        print('test done')
    except Exception as e:
        print(e)
        job.error_message = e
        job.ext_test_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def get_examples_and_labels(documents: List[Document]):
    examples: List[InputExample] = []
    labels = []
    for doc in documents:
        example = InputExample(id_=str(doc.id), s_id=doc.s_id, s_area_id=doc.s_area_id, title=doc.title,
                               author=doc.author,
                               content=doc.content,
                               post_time=doc.post_time)
        examples.append(example)
        labels.append([label.name for label in doc.labels.all()])
    return examples, labels


def create_ext_data(job: LabelingJob, uploaded_file, remove_old_data=True):
    if remove_old_data:
        job.document_set.filter(document_type=Document.TypeChoices.EXT_TEST).delete()
        job.save()
    create_documents(uploaded_file, job=job, document_type=Document.TypeChoices.EXT_TEST)


def get_model(job: ModelingJob, model_path=None, for_training=False, na_tag=None):
    # if job.model_path is None and model_path is None:

    if job.model_name in settings.ML_MODELS:
        model_cls = get_model_class(job.model_name)
        if issubclass(model_cls, RuleBaseModel):
            model_path = f"{job.id}_{job.name}"
        print(model_path)
        model: Union[SuperviseModel, RuleBaseModel] = model_cls(
            model_dir_name=model_path if model_path else job.model_path,
            feature=Features(job.feature), na_tag=na_tag)
        if hasattr(model, 'is_multi_label'):
            # print(job.is_multi_label)
            model.is_multi_label = job.is_multi_label
        if isinstance(model, SuperviseModel) and not for_training:
            model.load()
        elif isinstance(model, RuleBaseModel):
            rules = get_rules(job=job.jobRef)
            model.load(rules)
        return model
    else:
        raise ValueError(f"Unknown model: {job.model_name}")


def get_rules(job: LabelingJob):
    rules = defaultdict(list)
    for rule in job.rule_set.all():
        rules[rule.label.name] = rule.content
    return rules


def create_term_weights(job: ModelingJob, label_term_weight: Dict[str, List[Tuple[str, float]]]):
    job.termweight_set.all().delete()
    if not job.jobRef:
        job.jobRef = LabelingJob(name=f"「{job.name}」自動建立的任務",
                                 description=f"因「{job.name}」匯入而自動建立的任務",
                                 job_data_type=LabelingJob.DataTypes.TERM_WEIGHT_MODEL,
                                 created_by=job.created_by)
        job.jobRef.save()
        for label_str in label_term_weight.keys():
            job.jobRef.label_set.create(name=label_str)
        job.jobRef.save()
    label_dict = job.jobRef.get_labels_dict()
    for label_str, term_weights in label_term_weight.items():
        for term, weight in term_weights:
            if label_str in label_dict:
                job.termweight_set.create(term=term, weight=weight, label=label_dict.get(label_str))
    job.save()


def get_term_weights(job: ModelingJob) -> Dict[str, List[Tuple[str, float]]]:
    label_term_weight: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for term_weight in job.termweight_set.all():
        label_term_weight[term_weight.label.name].append((term_weight.term, float(term_weight.weight),))
    return label_term_weight


def eval_dataset(model, job: ModelingJob, dataset, dataset_type: Document.TypeChoices):
    examples, y_true = get_examples_and_labels(dataset)
    report = model.eval(examples, y_true=y_true)
    print(report)
    report_json = json.dumps(report, ensure_ascii=False)
    tmp_report = job.report_set.create(dataset_type=dataset_type, report=report_json,
                                       accuracy=report.get('accuracy', -1))

    predict_labels, predict_logits = model.predict(examples)
    labels = {_label.name: _label for _label in job.jobRef.label_set.all()}
    print(labels)
    for doc, pred in zip(dataset, predict_labels):
        # process prediction
        pr = tmp_report.evalprediction_set.create(document=doc)
        if isinstance(pred, QuerySet):
            for _pred in pred:
                pr.prediction_labels.add(_pred)
        elif isinstance(pred, List):
            for _pred in pred:
                if isinstance(_pred, str):
                    pr_label = labels.get(_pred)
                    pr.prediction_labels.add(pr_label)
                    # print(pr)
                if isinstance(_pred, Label):
                    pr.prediction_labels.add(_pred)
        elif isinstance(pred, str):
            pr_label = labels.get(pred)
            pr.prediction_labels.add(pr_label)
        elif isinstance(pred, Label):
            pr.prediction_labels.add(labels.get(pred))
        else:
            raise ValueError(f"Unknown prediction data format {type(pred)}")
        pr.save()
