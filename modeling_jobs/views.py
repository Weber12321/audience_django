from collections import namedtuple

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django_q.tasks import AsyncTask

from core.helpers.data_helpers import parse_report, insert_csv_to_db
from labeling_jobs.models import LabelingJob, Document
from .forms import ModelingJobForm
from .models import ModelingJob, Report
from .tasks import train_model_task, testing_model_via_ext_data_task
import json


class IndexView(LoginRequiredMixin, ListView):
    model = ModelingJob
    template_name = "modeling_jobs/index.html"
    context_object_name = 'modeling_jobs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ml_model_list'] = [choice[0] for choice in ModelingJob.model_choices]
        context['job_list'] = LabelingJob.objects.all()
        return context


class JobDetailView(LoginRequiredMixin, generic.DetailView):
    model = ModelingJob
    context_object_name = 'job'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'modeling_jobs/detail.html'


class JobCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = ModelingJobForm
    template_name = 'modeling_jobs/add_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = ModelingJob
    form_class = ModelingJobForm
    template_name = 'modeling_jobs/update_form.html'

    def get_success_url(self):
        pk = self.kwargs.get("pk")
        return reverse('modeling_jobs:job-detail', kwargs={"pk": pk})


class JobDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = ModelingJob
    success_url = reverse_lazy('modeling_jobs:index')
    template_name = 'modeling_jobs/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            print(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(JobDeleteView, self).post(request, *args, **kwargs)


class ReportDetail(SingleObjectMixin, generic.ListView):
    paginate_by = 10
    model = Report

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'reports/report_detail.html'

    def get(self, request, *args, **kwargs):
        self.object: Report = self.get_object(queryset=Report.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        return context

    def get_queryset(self):
        return self.object.evalprediction_set.order_by('pk')


class DocDeleteView(LoginRequiredMixin, DetailView):
    model = LabelingJob

    def post(self, request):
        print(request.POST)


@csrf_exempt
def doc_delete(request):
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
    modelingJob.model_type = request.POST['model_type']
    modelingJob.save()
    return HttpResponse("Successfully creating a task")


@csrf_exempt
def update_task(request):
    m = ModelingJob.objects.get(id=request.POST['id'])
    m.name = request.POST['model_name']
    m.model_type = request.POST['model_type']
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
    result = insert_csv_to_db(file, job_id)
    return HttpResponse(result)


@csrf_exempt
def training_model(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    print(job.is_multi_label)
    a = AsyncTask(train_model_task, job=job, group='training_model')
    a.run()
    return HttpResponseRedirect(reverse('modeling_jobs:index'))


@csrf_exempt
def testing_model_via_ext_data(request, pk):
    uploaded_file = request.FILES['ext_test_file']
    job_train_status = ModelingJob.objects.get(pk=pk).job_train_status
    # python manage.py qcluster
    if job_train_status != 'done':
        return HttpResponse('請先訓練模型')
    else:
        job = ModelingJob.objects.get(pk=pk)
        a = AsyncTask(testing_model_via_ext_data_task, uploaded_file=uploaded_file, job=job, group='ext_test_model')
        a.run()
        return HttpResponse("Done")


@csrf_exempt
def result_page(request, modeling_job_id):
    report = ModelingJob.objects.get(pk=modeling_job_id).report_set.last()
    reports: dict = parse_report(report.report)
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


def get_progress(request, pk):
    job = ModelingJob.objects.get(pk=pk)

    response_data = {
        'state': job.job_train_status,
        'details': job.job_train_status,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')
