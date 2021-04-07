from labeling_jobs.models import LabelingJob, Document
from .models import ModelingJob, MLModel
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from modeling_jobs.helpers.data_helpers import DataHelper
from modeling_jobs.helpers.model_helpers import RuleModel, KeywordModel, ProbModel, RFModel, SvmModel, XgboostModel
from django.template.response import TemplateResponse
from django.shortcuts import render,redirect
from collections import namedtuple

class IndexView(LoginRequiredMixin, ListView):
    model = ModelingJob
    template_name = "modeling_jobs/index.html"
    context_object_name = 'modeling_jobs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ml_model_list'] = MLModel.objects.all()
        context['job_list'] = LabelingJob.objects.all()
        return context


class modelInfoView(LoginRequiredMixin, DetailView):
    model = LabelingJob
    template_name = "modeling_jobs/model_info.html"


class docDeleteView(LoginRequiredMixin, DetailView):
    model = LabelingJob

    def post(self, request):
        print(request.POST)


@csrf_exempt
def docDelete(request, model_id):
    doc_id = request.POST["doc_id"]
    doc = Document.objects.filter(id=doc_id)
    doc.delete()
    return HttpResponse("You're deleting on id %s." % doc_id)


@csrf_exempt
def docUpdate(request, model_id):
    doc_id = request.POST["id"]
    doc = Document.objects.get(id=doc_id)
    doc.title = request.POST["title"]
    doc.author = request.POST["author"]
    doc.s_area_id = request.POST["s_area_id"]
    doc.content = request.POST["content"]
    doc.save()
    return HttpResponse("You're updating on id %s." % doc_id)


@csrf_exempt
def createTask(request):
    modelingJob = ModelingJob()
    modelingJob.name = request.POST['model_name']
    modelingJob.description = request.POST['description']
    modelingJob.is_multi_label = request.POST['is_multi_label']
    modelingJob.jobRef_id = request.POST['ref_job']
    modelingJob.model_id = request.POST['model_type']
    modelingJob.save()
    return HttpResponse("Successfully creating a task")


@csrf_exempt
def updateTask(request):
    m = ModelingJob.objects.get(id=request.POST['id'])
    m.name = request.POST['model_name']
    m.model_id = request.POST['model_type']
    m.description = request.POST['description']
    m.is_multi_label = request.POST['is_multi_label']
    m.jobRef_id = request.POST['ref_job']
    m.save()
    return HttpResponse("Successfully update the task")


@csrf_exempt
def deleteTask(request):
    m = ModelingJob.objects.get(id=request.POST['id'])
    m.delete()
    return HttpResponse("Successfully delete!")


@csrf_exempt
def insert_csv(request):
    file = request.FILES['file']
    job_id = request.POST['job_id']
    dataHelper = DataHelper()
    result = dataHelper.insert_csv_to_db(file, job_id)
    return HttpResponse(result)


@csrf_exempt
def training_model(request):
    jobRef_id = request.POST['jobRef_id']
    model_type = request.POST['model']
    is_multi_label = request.POST['is_multi_label']
    modeling_job_id = request.POST['modeling_job_id']
    dataHelper = DataHelper()
    content, labels = dataHelper.get_training_data(jobRef_id)
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
            svmModel.fit(content, labels ,modeling_job_id)
        else:
            svmModel.multi_fit(content, labels,modeling_job_id)
    elif model_type == 'XGBOOST_MODEL':
        xgboostModel = XgboostModel()
        if is_multi_label == "False":
            xgboostModel.fit(content, labels, modeling_job_id)
        else:
            xgboostModel.multi_fit(content, labels, modeling_job_id)
    return HttpResponse("Done")

@csrf_exempt
def testing_model(request):
    file = request.FILES['file']
    modeling_job_id = request.POST['job_id']
    model_type = request.POST['model_type']
    is_multi_label = request.POST['is_multi_label']
    dataHelper = DataHelper()
    content,labels = dataHelper.get_test_data(file)
    if content == [] and labels == []:
        return HttpResponse("False")
    else:
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
                result = svmModel.predict(content,labels,modeling_job_id)
            else:
                svmModel.predict_multi_label(content,labels,modeling_job_id)
        elif model_type == 'XGBOOST_MODEL':
            xgboostModel = XgboostModel()
            if is_multi_label == 'False':
                result = xgboostModel.predict(content, labels, modeling_job_id)
            else:
                xgboostModel.predict_multi_label(content, labels, modeling_job_id)
        return HttpResponse('Done')

@csrf_exempt
def result_page(request,modeling_job_id):
    dataHelper = DataHelper()
    reports : dict = dataHelper.get_report(modeling_job_id)
    accuracy = reports.pop('accuracy')
    macro_avg = reports.pop('macro avg')
    macro_avg['f1_score'] = macro_avg['f1-score']
    weighted_avg = reports.pop('weighted avg')
    weighted_avg['f1_score'] = weighted_avg['f1-score']
    label_info = namedtuple('label_info', ['label','precision', 'recall', 'f1_score','support'])
    labels = []
    for key in reports.keys():
        label = reports.get(key)
        s = label_info(key,label.get('precision'),label.get('recall'),label.get('f1-score'),label.get('support'))
        labels.append(s)
    return render(request,'modeling_jobs/result.html',{"accuracy" : accuracy,
                                                       "macro_avg" : macro_avg,
                                                       "weighted_avg" : weighted_avg,
                                                       "labels" : labels})