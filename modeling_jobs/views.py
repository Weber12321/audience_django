from django_q.tasks import AsyncTask

from labeling_jobs.models import LabelingJob, Document
from .models import ModelingJob, MLModel
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from core.helpers.data_helpers import DataHelper
from django.shortcuts import render
from collections import namedtuple
from .tasks import train_model, test_model
from django_q.tasks import AsyncTask


class IndexView(LoginRequiredMixin, ListView):
    model = ModelingJob
    template_name = "modeling_jobs/index.html"
    context_object_name = 'modeling_jobs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ml_model_list'] = MLModel.objects.all()
        context['job_list'] = LabelingJob.objects.all()
        return context


class ModelInfoView(LoginRequiredMixin, DetailView):
    model = LabelingJob
    template_name = "modeling_jobs/model_info.html"


class DocDeleteView(LoginRequiredMixin, DetailView):
    model = LabelingJob

    def post(self, request):
        print(request.POST)


@csrf_exempt
def doc_delete(request, model_id):
    doc_id = request.POST["doc_id"]
    doc = Document.objects.filter(id=doc_id)
    doc.delete()
    return HttpResponse("You're deleting on id %s." % doc_id)


@csrf_exempt
def doc_update(request, model_id):
    doc_id = request.POST["id"]
    doc = Document.objects.get(id=doc_id)
    doc.title = request.POST["title"]
    doc.author = request.POST["author"]
    doc.schema = request.POST["s_area_id"]
    doc.content = request.POST["content"]
    doc.save()
    return HttpResponse("You're updating on id %s." % doc_id)


@csrf_exempt
def create_task(request):
    modelingJob = ModelingJob()
    modelingJob.name = request.POST['model_name']
    modelingJob.description = request.POST['description']
    modelingJob.is_multi_label = request.POST['is_multi_label']
    modelingJob.jobRef_id = request.POST['ref_job']
    modelingJob.model_id = request.POST['model_type']
    modelingJob.save()
    return HttpResponse("Successfully creating a task")


@csrf_exempt
def update_task(request):
    m = ModelingJob.objects.get(id=request.POST['id'])
    m.name = request.POST['model_name']
    m.model_id = request.POST['model_type']
    m.description = request.POST['description']
    m.is_multi_label = request.POST['is_multi_label']
    m.jobRef_id = request.POST['ref_job']
    m.save()
    return HttpResponse("Successfully update the task")


@csrf_exempt
def delete_task(request):
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

    job = ModelingJob.objects.get(pk=modeling_job_id)
    a = AsyncTask(train_model, model_type=model_type, content=content, labels=labels, is_multi_label=is_multi_label,
                  modeling_job_id=modeling_job_id, job=job, group='training_model')
    a.run()
    return HttpResponse("進行中")


@csrf_exempt
def testing_model(request):
    file = request.FILES['file']
    modeling_job_id = request.POST['job_id']
    model_type = request.POST['model_type']
    is_multi_label = request.POST['is_multi_label']
    dataHelper = DataHelper()
    content, labels = dataHelper.get_test_data(file)
    job_train_status = ModelingJob.objects.get(pk=modeling_job_id).job_train_status

    if job_train_status != 'done':
        return HttpResponse('請先訓練模型')

    elif content == [] and labels == []:
        return HttpResponse('欄位不符合')

    else:
        job = ModelingJob.objects.get(pk=modeling_job_id)
        a = AsyncTask(test_model, model_type=model_type, content=content, labels=labels, is_multi_label=is_multi_label,
                      modeling_job_id=modeling_job_id, job=job, group='test_model')
        a.run()
        return HttpResponse("Done")


@csrf_exempt
def result_page(request, modeling_job_id):
    dataHelper = DataHelper()
    reports: dict = dataHelper.get_report(modeling_job_id)
    accuracy = reports.pop('accuracy')
    macro_avg = reports.pop('macro avg')
    macro_avg['f1_score'] = macro_avg['f1-score']
    weighted_avg = reports.pop('weighted avg')
    weighted_avg['f1_score'] = weighted_avg['f1-score']
    label_info = namedtuple('label_info', ['label', 'precision', 'recall', 'f1_score', 'support'])
    labels = []
    for key in reports.keys():
        label = reports.get(key)
        s = label_info(key, label.get('precision'), label.get('recall'), label.get('f1-score'), label.get('support'))
        labels.append(s)
    return render(request, 'modeling_jobs/result.html', {"accuracy": accuracy,
                                                         "macro_avg": macro_avg,
                                                         "weighted_avg": weighted_avg,
                                                         "labels": labels})
