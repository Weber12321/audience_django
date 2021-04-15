import importlib

from audience_toolkits import settings
from core.audience.models.base_model import AudienceModel
from labeling_jobs.models import Document
from modeling_jobs.models import ModelingJob, Report


def get_model_class(name: str):
    """
    藉由settings中的ML_MODELS的設定讀取機器學習模型模組
    :param name: 設定中的模組名稱
    :return: AudienceModel Class
    """
    mod_path, class_name = settings.ML_MODELS.get(name).get('module').rsplit(sep='.', maxsplit=1)
    return getattr(importlib.import_module(mod_path), class_name)


def train_model(job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    contents, labels = get_training_data(job.jobRef.id)

    model_path = f"{job.id}_{job.name}"
    if job.model_type in settings.ML_MODELS:
        model_cls = get_model_class(job.model_type)
        model: AudienceModel = model_cls(model_dir_name=model_path)
        if hasattr(model, 'is_multi_label'):
            model.is_multi_label = job.is_multi_label
    else:
        raise ValueError(f"Unknown model_type: {job.model_type}")
    job.model_path = model.fit(contents=contents, y_true=labels)

    job.job_train_status = ModelingJob.JobStatus.DONE
    job.save()
    print('training done')


def test_model(contents, y_true, job: ModelingJob):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    if job.model_type in settings.ML_MODELS:
        model_cls = get_model_class(job.model_type)
        model: AudienceModel = model_cls(model_dir_name=job.model_path)
        if hasattr(model, 'is_multi_label'):
            model.is_multi_label = job.is_multi_label
    else:
        raise ValueError(f"Unknown model_type: {job.model_type}")
    model.load()
    report = model.eval(contents, y_true=y_true)
    save_report(modeling_job_id=job.id, report=report)
    job.job_test_status = ModelingJob.JobStatus.DONE
    job.save()
    print('test done')


def save_report(modeling_job_id, report):
    data = Report.objects.filter(models_ref_id=modeling_job_id)
    accuracy = report.get('accuracy', -1)
    if len(data) == 0:
        r = Report(accuracy=accuracy, report=str(report), models_ref_id=modeling_job_id)
        r.save()
    else:
        data.update(accuracy=accuracy, report=report)


def get_training_data(labeling_job_id):
    documents = Document.objects.filter(labeling_job_id=labeling_job_id)
    content = []
    labels = []
    for doc in documents:
        content.append(doc.content)
        labels.append([label.name for label in doc.labels.all()])
    return content, labels
