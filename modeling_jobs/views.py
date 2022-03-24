import codecs
import csv
import json
import logging
from io import StringIO, BytesIO

import cchardet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from rest_framework import viewsets, permissions

from audience_toolkits.settings import API_PATH
from labeling_jobs.models import LabelingJob, Document
from .forms import ModelingJobForm, TermWeightForm, UploadModelJobForm
from .helpers import insert_csv_to_db
from .models import ModelingJob, TermWeight, UploadModelJob
from .serializers import JobSerializer, TermWeightSerializer
from .tasks import call_model_preparing, \
    call_model_testing, process_report, get_progress_api, call_model_import, get_report_details, \
    get_detail_file_link, call_download_details, call_get_term_weights, call_term_weight_download, call_term_weight_add, \
    call_term_weight_update, call_term_weight_delete

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
    model = ModelingJob
    template_name = "modeling_jobs/index.html"
    form_class = ModelingJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ml_model_list'] = [choice[1] for choice in ModelingJob.__model_choices__]
        context['job_list'] = LabelingJob.objects.all()
        context["modeling_jobs"] = self.model.objects.order_by('-created_at')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class JobDetailAndUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = ModelingJob
    form_class = ModelingJobForm
    template_name = 'job_details/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job"] = self.object

        if self.object.model_name == "TERM_WEIGHT_MODEL":
            import_model_form = UploadModelJobForm({'modeling_job': self.object.id, })
            context["import_model_form"] = import_model_form
            term_form = TermWeightForm(modeling_job=self.object.id)
            context['term_weight'] = call_get_term_weights(task_id=self.object.task_id.hex)
            context['term_form'] = term_form
            context['api_link'] = f'{API_PATH}/models'
            context['task_id'] = self.object.task_id.hex
        return context

    def get_template_names(self):
        logger.debug(self.object.model_name)
        if self.object.model_name == "TERM_WEIGHT_MODEL":
            return 'job_details/term_weight_detail.html'
        else:
            return 'job_details/detail.html'

    def get_success_url(self):
        _pk = self.kwargs['pk']
        return reverse_lazy('modeling_jobs:job-detail', kwargs={'pk': _pk})


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
            logger.debug(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(JobDeleteView, self).post(request, *args, **kwargs)


# class ReportDetail(SingleObjectMixin, generic.ListView):
#     paginate_by = 10
#     model = Report
#
#     # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
#     template_name = 'reports/report_detail.html'
#
#     def get(self, request, *args, **kwargs):
#         self.object: Report = self.get_object(queryset=Report.objects.all())
#         return super().get(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['report'] = self.object
#         return context
#
#     def get_queryset(self):
#         return self.object.evalprediction_set.order_by('pk')


class DocDeleteView(LoginRequiredMixin, DetailView):
    model = LabelingJob

    def post(self, request):
        logger.debug(request.POST)


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
    modelingJob.model_name = request.POST['model_type']
    modelingJob.save()
    return HttpResponse("Successfully creating a task")


@csrf_exempt
def update_task(request):
    m = ModelingJob.objects.get(id=request.POST['id'])
    m.name = request.POST['model_name']
    m.model_name = request.POST['model_type']
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
    logger.debug(job.is_multi_label)
    # a = AsyncTask(train_model_task, job=job, group='training_model')
    # a.run()
    call_model_preparing(job=job)
    return HttpResponseRedirect(reverse('modeling_jobs:index'))


@csrf_exempt
def testing_model_via_ext_data(request, pk):
    uploaded_file = request.FILES['ext_test_file']
    job_train_status = ModelingJob.objects.get(pk=pk).job_status
    # python manage.py qcluster
    if job_train_status != 'done':
        return HttpResponse('請先訓練模型')
    else:
        job = ModelingJob.objects.get(pk=pk)
        # a = AsyncTask(testing_model_via_ext_data_task, uploaded_file=uploaded_file, job=job, group='ext_test_model')
        # a.run()
        call_model_testing(uploaded_file, job=job, remove_old_data=True)
        return HttpResponseRedirect(reverse('modeling_jobs:job-detail', kwargs={"pk": pk}))


@csrf_exempt
def result_page(request, modeling_job_id):
    # report = ModelingJob.objects.get(pk=modeling_job_id).report_set.last()
    # reports: dict = parse_report(report.report)
    # accuracy = reports.pop('accuracy')
    # macro_avg = reports.pop('macro avg')
    # macro_avg['f1_score'] = macro_avg['f1-score']
    # weighted_avg = reports.pop('weighted avg')
    # weighted_avg['f1_score'] = weighted_avg['f1-score']
    # label_info = namedtuple('label_info', ['label', 'precision', 'recall', 'f1_score', 'support'])
    # labels = []
    # for key in reports.keys():
    #     label = reports.get(key)
    #     s = label_info(key, label.get('precision'), label.get('recall'), label.get('f1-score'), label.get('support'))
    #     labels.append(s)
    job = ModelingJob.objects.get(pk=modeling_job_id)

    report_dict = process_report(task_id=job.task_id.hex)

    return render(request, 'modeling_jobs/result.html', report_dict)


def get_progress(request, pk):
    job = get_progress_api(pk=pk)
    report_dict = get_report_details(task_id=job.task_id.hex)
    detail_download_links = get_detail_file_link(task_id=job.task_id.hex)

    if job.model_name in {"TERM_WEIGHT_MODEL"}:
        response_data = {
            'state': job.job_status,
            'details': job.error_message if job.job_status == ModelingJob.JobStatus.ERROR else job.job_status,
            'report': report_dict,
            # 'download_links': detail_download_links,
            'base_api': f'{API_PATH}/models',
            'task_id': job.task_id.hex,
            # 'term_weight_set': call_get_term_weight_set(task_id=job.task_id)
            # 'term_weight_set': get_term_weights_datatables(task_id=job.task_id.hex)
        }
        return HttpResponse(json.dumps(response_data), content_type='application/json')
    else:
        response_data = {
            'state': job.job_status,
            'details': job.error_message if job.job_status == ModelingJob.JobStatus.ERROR else job.job_status,
            'report': report_dict,
            # 'download_links': detail_download_links,
            'base_api': f'{API_PATH}/models'
        }
        return HttpResponse(json.dumps(response_data), content_type='application/json')


def render_reports(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    template = loader.get_template('reports/report_detail.html')
    context = {
        'task_id': job.task_id.hex
    }

    return HttpResponse(template.render(context, request))


@csrf_exempt
def download_model_details(request, pk, data_type):
    job = ModelingJob.objects.get(pk=pk)
    file_path = call_download_details(task_id=job.task_id.hex, data_type=data_type)
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = "application/vnd.ms-excel"
    response['Content-Disposition'] = f'attachment;filename="{job.task_id.hex}_{data_type}.csv"'
    return response


@csrf_exempt
def download_term_weights(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    template = loader.get_template('job_details/error_page.html')
    response = call_term_weight_download(task_id=job.task_id.hex)
    if hasattr(response, 'status_code'):
        """`response` should be filepath if download API response 200 
        otherwise it return response data structure"""

        context = {
            'error_code': response.status_code,
            'error_message': "錯誤訊息: " + f"{response.json()}"
        }
        return HttpResponse(template.render(context, request))

    file_response = FileResponse(open(response, 'rb'))
    file_response['Content-Type'] = "application/vnd.ms-excel"
    file_response['Content-Disposition'] = f'attachment;filename="{job.task_id.hex}_term_weight.csv"'
    return file_response


@csrf_exempt
def add_term_weight(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    template = loader.get_template('job_details/error_page.html')
    if request.method == "POST":
        response = call_term_weight_add(task_id=job.task_id.hex,
                                        label=request.POST.get('label'),
                                        term=request.POST.get('term'),
                                        weight=request.POST.get('weight'))
        if response.status_code == 200:
            return HttpResponseRedirect(reverse('modeling_jobs:job-detail', kwargs={"pk": pk}))
        else:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))


@csrf_exempt
def update_term_weight(request, pk):
    template = loader.get_template('job_details/error_page.html')
    if request.method == 'POST':
        response = call_term_weight_update(term_weight_id=request.POST.get('update_id'),
                                           label=request.POST.get('update_label'),
                                           term=request.POST.get('update_term'),
                                           weight=request.POST.get('update_weight'))
        if response.status_code == 200:
            return HttpResponseRedirect(reverse('modeling_jobs:job-detail', kwargs={"pk": pk}))
        else:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))


@csrf_exempt
def delete_term_weight(request, pk):
    template = loader.get_template('job_details/error_page.html')
    if request.method == 'POST':
        response = call_term_weight_delete(term_weight_id=request.POST.get('delete_id'))

        if response.status_code == 200:
            return HttpResponseRedirect(reverse('modeling_jobs:job-detail', kwargs={"pk": pk}))
        else:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))


@csrf_exempt
def upload_term_weight(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    template = loader.get_template('job_details/error_page.html')
    if request.method == 'POST':
        file = request.FILES.get('term_file')
        # file.seek(0)
        # file_handle = BytesIO(file.read())
        # encoding = cchardet.detect(file.read())['encoding']
        # file.seek(0)
        # csv_file = csv.DictReader(codecs.iterdecode(file, encoding))
        response = call_model_import(task_id=job.task_id.hex, file=file)
        # response = 200 if file else 500
        if response.status_code == 200:
            return HttpResponseRedirect(reverse('modeling_jobs:job-detail', kwargs={"pk": pk}))
        else:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))


def render_term_weight(request, pk):
    job = ModelingJob.objects.get(pk=pk)
    response = call_get_term_weights(task_id=job.task_id.hex)
    return HttpResponse(json.dumps(response.json()), content_type='application/json')



# class TermWeightUpdate(LoginRequiredMixin, generic.UpdateView):
#     model = TermWeight
#     form_class = TermWeightForm
#     template_name = 'term_weights/update_form.html'

#
# class TermWeightCreate(LoginRequiredMixin, generic.CreateView):
#     form_class = TermWeightForm
#     template_name = 'term_weights/add_form.html'
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['modeling_job'] = self.kwargs.get('job_id')
#         return kwargs
#
#     def form_valid(self, form):
#         form.instance.modeling_job_id = self.kwargs.get('job_id')
#         return super(TermWeightCreate, self).form_valid(form)
#
#     def get_success_url(self):
#         job_id = self.kwargs.get('job_id')
#         return reverse_lazy('modeling_jobs:job-detail', kwargs={"pk": job_id})
#
#
# class TermWeightDelete(LoginRequiredMixin, generic.DeleteView):
#     model = TermWeight
#     # success_url = reverse_lazy('predicting_jobs:index')
#     template_name = 'term_weights/confirm_delete_form.html'
#
#     def post(self, request, *args, **kwargs):
#         if "cancel" in request.POST:
#             logger.debug(request.POST)
#             return HttpResponseRedirect(self.get_success_url())
#         else:
#             return super(TermWeightDelete, self).post(request, *args, **kwargs)
#
#     def get_success_url(self):
#         job_id = self.kwargs.get('pk')
#         return reverse_lazy('modeling_job_id:job-detail', kwargs={"pk": job_id})


# class UploadModelJobCreate(LoginRequiredMixin, generic.CreateView):
#     model = UploadModelJob
#     form_class = UploadModelJobForm
#     template_name = 'model_upload/file_upload_form.html'
#
#     def get_success_url(self):
#         # 利用django-q實作非同步上傳
#           a = AsyncTask(import_model_data_task, upload_job=self.object, group='upload_model')
#         # a.run()
#         call_model_import(upload_job=self.object)
#         job_id = self.kwargs['job_id']
#         return reverse_lazy('modeling_jobs:job-detail', kwargs={'pk': job_id})
#
#     def form_valid(self, form):
#         logger.debug(self.kwargs)
#         form.instance.modeling_job_id = self.kwargs.get('job_id')
#         form.instance.created_by = self.request.user
#         logger.debug(form.instance)
#         return super(UploadModelJobCreate, self).form_valid(form)


class UploadModelJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = UploadModelJob
    template_name = 'model_upload/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            logger.debug(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(UploadModelJobDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('modeling_jobs:job-detail', kwargs={"pk": job_id})


# rest api views

class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ModelingJob.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]


class TermWrightViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = TermWeight.objects.all().order_by('-weight')
    serializer_class = TermWeightSerializer
    # filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    # search_fields = ['term', 'label__name']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        logger.debug(self.basename)
        job_id = self.request.query_params.get('job')
        if job_id is not None:
            return TermWeight.objects.filter(modeling_job_id=job_id).order_by('-weight')
        else:
            return TermWeight.objects.all().order_by('-weight')


def render_term_add(request, job_id):
    job = ModelingJob.objects.get(pk=job_id)
    template = loader.get_template('term_weights/add_form.html')
    context = {"job": job, "task_id": job.task_id.hex, "api_link": f'{API_PATH}/models'}
    return HttpResponse(template.render(context, request))
