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


def train_model_task(job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    train_set = job.jobRef.get_train_set()

    contents, y_true = get_feature_and_label(train_set)

    model_path = f"{job.id}_{job.name}"
    if job.model_type in settings.ML_MODELS:
        model_cls = get_model_class(job.model_type)
        model: AudienceModel = model_cls(model_dir_name=model_path)
        if hasattr(model, 'is_multi_label'):
            model.is_multi_label = job.is_multi_label
    else:
        raise ValueError(f"Unknown model_type: {job.model_type}")
    job.model_path = model.fit(contents=contents, y_true=y_true)

    job.job_train_status = ModelingJob.JobStatus.DONE
    job.save()
    print('training done')


def test_model_task(job: ModelingJob):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()

    test_set = job.jobRef.get_test_set()

    contents, y_true = get_feature_and_label(test_set)

    if job.model_type in settings.ML_MODELS:
        model_cls = get_model_class(job.model_type)
        model: AudienceModel = model_cls(model_dir_name=job.model_path)
        if hasattr(model, 'is_multi_label'):
            model.is_multi_label = job.is_multi_label
    else:
        raise ValueError(f"Unknown model_type: {job.model_type}")
    model.load()
    report = model.eval(contents, y_true=y_true)
    job.report_set.create(dataset_type=Document.TypeChoices.TEST, report=report, accuracy=report.get('accuracy', -1))
    job.save()
    # save_report(modeling_job_id=job.id, report=report)
    job.job_test_status = ModelingJob.JobStatus.DONE
    job.save()
    print('test done')


def test_model_via_ext_data(contents, y_true, job: ModelingJob):
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
    job.report_set.create(dataset_type=Document.TypeChoices.TEST, report=report, accuracy=report.get('accuracy', -1))
    job.save()
    # save_report(modeling_job_id=job.id, report=report)
    job.job_test_status = ModelingJob.JobStatus.DONE
    job.save()
    print('test done')


# def save_report(modeling_job_id, report):
#     report =
#     data = Report.objects.filter(models_ref_id=modeling_job_id)
#     accuracy = report.get('accuracy', -1)
#     if len(data) == 0:
#         r = Report(accuracy=accuracy, report=str(report), models_ref_id=modeling_job_id)
#         r.save()
#     else:
#         data.update(accuracy=accuracy, report=report)


def get_feature_and_label(documents):
    content = []
    labels = []
    for doc in documents:
        content.append(doc.content)
        labels.append([label.name for label in doc.labels.all()])
    return content, labels
