from audience_toolkits import settings
from labeling_jobs.models import Document
from modeling_jobs.models import ModelingJob, Report
from core.audience.models.classic.svm_model import SvmModel
from core.audience.models.classic.term_weight_model import TermWeightModel
from core.audience.models.classic.random_forest_model import RandomForestModel
from core.audience.models.rule_base.keyword_base_model import KeywordModel
from core.audience.models.rule_base.regex_model import RegexModel


def train_model(job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    contents,labels = get_training_data(job.jobRef.id)

    model_type = job.model.name
    model_path = f"{job.id}_{job.name}"
    if model_type == 'RULE_MODEL':
        model = RegexModel(model_dir_name=model_path)
    elif model_type == 'KEYWORD_MODEL':
        model = KeywordModel(model_dir_name=model_path)
    elif model_type == 'PROB_MODEL':
        model = TermWeightModel(model_dir_name=model_path)
    elif model_type == 'RF_MODEL':
        model = RandomForestModel(model_dir_name=model_path)
    elif model_type == 'SVM_MODEL':
        model = SvmModel(model_dir_name=model_path, is_multi_label=job.is_multi_label)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    job.model_path = model.fit(contents=contents, y_true=labels)

    job.job_train_status = ModelingJob.JobStatus.DONE
    job.save()
    print('training done')


def test_model(contents, y_true, job: ModelingJob):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    model_type = job.model.name
    if model_type == 'RULE_MODEL':
        model = RegexModel(model_dir_name=job.model_path)
    elif model_type == 'KEYWORD_MODEL':
        model = KeywordModel(model_dir_name=job.model_path)
    elif model_type == 'PROB_MODEL':
        model = TermWeightModel(model_dir_name=job.model_path)
    elif model_type == 'RF_MODEL':
        model = RandomForestModel(model_dir_name=job.model_path)
    elif model_type == 'SVM_MODEL':
        model = SvmModel(model_dir_name=job.model_path, is_multi_label=job.is_multi_label)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
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
