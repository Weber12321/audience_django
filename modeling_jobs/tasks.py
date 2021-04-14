from modeling_jobs.models import ModelingJob
from core.audience.models.classic.svm_model import SvmModel
from core.audience.models.classic.term_weight_model import TermWeightModel
from core.audience.models.classic.random_forest_model import RandomForestModel
from core.audience.models.rule_base.keyword_base_model import KeywordModel
from core.audience.models.rule_base.regex_model import RegexModel


def train_model(model_type, contents, labels, job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    model_path = f"{job.id}_{job.name}"
    if model_type == 'RULE_MODEL':
        model = RegexModel(model_dir_path=model_path)
    elif model_type == 'KEYWORD_MODEL':
        model = KeywordModel(model_dir_path=model_path)
    elif model_type == 'PROB_MODEL':
        model = TermWeightModel(model_dir_path=model_path)
    elif model_type == 'RF_MODEL':
        model = RandomForestModel(model_dir_path=model_path)
    elif model_type == 'SVM_MODEL':
        model = SvmModel(model_dir_path=model_path, is_multi_label=job.is_multi_label)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    job.model_path = model.fit(contents=contents, y_true=labels)

    job.job_train_status = ModelingJob.JobStatus.DONE
    job.save()
    print('training done')


def test_model(model_type, content, y_true, job: ModelingJob):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    if model_type == 'RULE_MODEL':
        model = RegexModel(model_dir_path=job.model_path)
    elif model_type == 'KEYWORD_MODEL':
        model = KeywordModel(model_dir_path=job.model_path)
    elif model_type == 'PROB_MODEL':
        model = TermWeightModel(model_dir_path=job.model_path)
    elif model_type == 'RF_MODEL':
        model = RandomForestModel(model_dir_path=job.model_path)
    elif model_type == 'SVM_MODEL':
        model = SvmModel(model_dir_path=job.model_path, is_multi_label=job.is_multi_label)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    model.eval(content, y_true=y_true)

    job.job_test_status = ModelingJob.JobStatus.DONE
    job.save()
    print('test done')
