import json
from collections import defaultdict
from typing import List, Union

from django.db import IntegrityError
from django.db.models import QuerySet

from audience_toolkits import settings
from core.audience.models.base_model import SuperviseModel, RuleBaseModel
from core.dao.input_example import Features, InputExample
from core.helpers.model_helpers import get_model_class
from labeling_jobs.models import Document, LabelingJob, Label
from labeling_jobs.tasks import create_documents
from modeling_jobs.models import ModelingJob


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
