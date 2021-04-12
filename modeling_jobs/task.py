from modeling_jobs.models import ModelingJob
from core.helpers.model_helpers import RuleModel, KeywordModel, ProbModel, RFModel, SvmModel, XgboostModel


def train_model(model_type, content, labels, is_multi_label, modeling_job_id, job: ModelingJob):
    job.job_train_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    if model_type == 'RULE_MODEL':
        ruleModel = RuleModel()
    elif model_type == 'KEYWORD_MODEL':
        keywordModel = KeywordModel()
    elif model_type == 'PROB_MODEL':
        probModel = ProbModel()
    elif model_type == 'RF_MODEL':
        rfModel = RFModel()
    elif model_type == 'SVM_MODEL':
        svmModel = SvmModel()
        if is_multi_label == "False":
            model_path = svmModel.fit(content, labels, modeling_job_id)
        else:
            model_path = svmModel.multi_fit(content, labels, modeling_job_id)
    elif model_type == 'XGBOOST_MODEL':
        xgboostModel = XgboostModel()
        if is_multi_label == "False":
            model_path = xgboostModel.fit(content, labels, modeling_job_id)
        else:
            model_path = xgboostModel.multi_fit(content, labels, modeling_job_id)


    job.model_path = model_path
    job.job_train_status = ModelingJob.JobStatus.DONE
    job.save()
    print('training done')

def test_model(model_type, content, labels, is_multi_label, modeling_job_id, job: ModelingJob):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    if model_type == 'RULE_MODEL':
        ruleModel = RuleModel()
    elif model_type == 'KEYWORD_MODEL':
        keywordModel = KeywordModel()
    elif model_type == 'PROB_MODEL':
        probModel = ProbModel()
    elif model_type == 'RF_MODEL':
        rfModel = RFModel()
    elif model_type == 'SVM_MODEL':
        svmModel = SvmModel()
        if is_multi_label == 'False':
            svmModel.predict(content, labels, modeling_job_id)
        else:
            svmModel.predict_multi_label(content, labels, modeling_job_id)
    elif model_type == 'XGBOOST_MODEL':
        xgboostModel = XgboostModel()
        if is_multi_label == 'False':
            xgboostModel.predict(content, labels, modeling_job_id)
        else:
            xgboostModel.predict_multi_label(content, labels, modeling_job_id)
    job.job_test_status = ModelingJob.JobStatus.DONE
    job.save()
    print('test done')
