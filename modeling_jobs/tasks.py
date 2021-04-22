import importlib
import json
from typing import List

from django.db.models import QuerySet

from audience_toolkits import settings
from core.audience.models.base_model import AudienceModel
from core.dao.input_example import Features, InputExample
from labeling_jobs.models import Document, LabelingJob, Label
from labeling_jobs.tasks import create_documents
from modeling_jobs.models import ModelingJob


def get_model_class(name: str):
    """
    藉由settings中的ML_MODELS的設定讀取機器學習模型模組
    :param name: 設定中的模組名稱
    :return: AudienceModel Class
    """
    mod_path, class_name = settings.ML_MODELS.get(name).get('module').rsplit(sep='.', maxsplit=1)
    return getattr(importlib.import_module(mod_path), class_name)


def train_model_task(job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        train_set = job.jobRef.get_train_set()
        contents, y_true = get_feature_and_label(train_set)
        model_path = f"{job.id}_{job.name}"
        model = load_model(job, model_path)

        job.model_path = model.fit(examples=contents, y_true=y_true)

        # get train set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.TRAIN, dataset=train_set, job=job)

        # get dev set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.DEV, dataset=job.jobRef.get_dev_set(), job=job)

        # get test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.TEST, dataset=job.jobRef.get_test_set(), job=job)

        job.job_train_status = ModelingJob.JobStatus.DONE
        job.save()
        print('training done')
    except Exception as e:
        print(e)
        job.job_train_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def testing_model_via_ext_data_task(uploaded_file, job: ModelingJob, remove_old_data=True):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        create_ext_data(uploaded_file=uploaded_file, job=job.jobRef, remove_old_data=remove_old_data)
        print(job.model_type, job.model_path, job.is_multi_label)
        model = load_model(job)
        print(model)
        model.load()
        # get ext test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.EXT_TEST, dataset=job.jobRef.get_ext_test_set(),
                     job=job)
        job.ext_test_status = ModelingJob.JobStatus.DONE
        print('test done')
    except Exception as e:
        print(e)
        job.ext_test_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def get_feature_and_label(documents: List[Document], feature=Features.CONTENT):
    examples: List[InputExample] = []
    labels = []
    for doc in documents:
        example = InputExample(id_=str(doc.id), s_area_id=doc.s_area_id, title=doc.title, author=doc.author,
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


def load_model(job: ModelingJob, model_path=None):
    if job.model_type in settings.ML_MODELS:
        model_cls = get_model_class(job.model_type)
        model: AudienceModel = model_cls(model_dir_name=model_path if model_path else job.model_path)
        if hasattr(model, 'is_multi_label'):
            print(job.is_multi_label)
            model.is_multi_label = job.is_multi_label
        return model
    else:
        raise ValueError(f"Unknown model_type: {job.model_type}")


def eval_dataset(model, job: ModelingJob, dataset, dataset_type: Document.TypeChoices):
    contents, y_true = get_feature_and_label(dataset)
    report = model.eval(contents, y_true=y_true)
    report_json = json.dumps(report, ensure_ascii=False)
    tmp_report = job.report_set.create(dataset_type=dataset_type, report=report_json,
                                       accuracy=report.get('accuracy', -1))

    predict_labels, predict_logits = model.predict(contents)
    labels = {_label.name: _label for _label in job.jobRef.label_set.all()}
    for doc, pred in zip(dataset, predict_labels):
        # process prediction
        pr = tmp_report.evalprediction_set.create(document=doc)
        if isinstance(pred, QuerySet):
            for _pred in pred:
                pr.prediction_labels.add(_pred)
        elif isinstance(pred, List):
            for _pred in pred:
                if isinstance(_pred, str):
                    pr_label = labels.get(pred)
                    pr.prediction_labels.add(labels.get(pr_label))
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
