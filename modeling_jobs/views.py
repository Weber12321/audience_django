import json
import logging
from collections import namedtuple

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django_q.tasks import AsyncTask
from rest_framework import viewsets, permissions

from core.audience.models.base_model import RuleBaseModel, SuperviseModel
from labeling_jobs.models import LabelingJob, Document
from .forms import ModelingJobForm, TermWeightForm, UploadModelJobForm
from .helpers import insert_csv_to_db, parse_report
from .models import ModelingJob, Report, TermWeight, UploadModelJob
from .serializers import JobSerializer, TermWeightSerializer
from .tasks import train_model_task, testing_model_via_ext_data_task, import_model_data_task, call_model_preparing, \
    call_model_testing, call_model_status, process_report, get_progress_api

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
            context['term_form'] = term_form
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
    report_dict = process_report(task_id=modeling_job_id)

    return render(request, 'modeling_jobs/result.html', report_dict)


def get_progress(request, pk):
    # job = ModelingJob.objects.get(pk=pk)
    # # 處理規則模型，因為不用訓練，所以只需要確認資料類型
    # if job.get_model_type() == RuleBaseModel.__name__:
    #     if job.jobRef:
    #         # 如果是一般的RuleBase
    #         if job.model_name == LabelingJob.DataTypes.RULE_BASE_MODEL.name \
    #                 and job.jobRef.job_data_type != LabelingJob.DataTypes.RULE_BASE_MODEL:
    #             job.error_message = f"Data type error, RuleBaseModel need rules in labeling job, not labeled data ({job.jobRef.job_data_type})."
    #             job.job_status = ModelingJob.JobStatus.ERROR
    #             job.save()
    #         # Regex
    #         elif job.model_name == "REGEX_MODEL" \
    #                 and job.jobRef.job_data_type != LabelingJob.DataTypes.REGEX_MODEL:
    #             job.error_message = f"Data type error, RegexModel need regex in labeling job, not labeled data ({job.jobRef.job_data_type})."
    #             job.job_status = ModelingJob.JobStatus.ERROR
    #             job.save()
    #         else:
    #             job.job_status = ModelingJob.JobStatus.DONE
    #             job.save()
    #     else:
    #         job.error_message = "No labeling job reference error."
    #         job.job_status = ModelingJob.JobStatus.ERROR
    #         job.save()
    #
    # elif job.get_model_type() == SuperviseModel.__name__:
    #     if job.jobRef:
    #         if job.model_name == "TERM_WEIGHT_MODEL":
    #             if job.jobRef.job_data_type not in {LabelingJob.DataTypes.TERM_WEIGHT_MODEL,
    #                                                 LabelingJob.DataTypes.SUPERVISE_MODEL}:
    #                 job.error_message = f"Data type error, TermWeightModel need labeled data in labeling job, not rules ({job.jobRef.job_data_type})."
    #                 job.job_status = ModelingJob.JobStatus.ERROR
    #                 job.save()
    #             else:
    #                 job.job_status = ModelingJob.JobStatus.DONE
    #                 job.save()
    #         else:
    #             if job.jobRef.job_data_type != LabelingJob.DataTypes.SUPERVISE_MODEL:
    #                 job.error_message = f"Data type error, SuperviseModel need labeled data in labeling job, not rules ({job.jobRef.job_data_type})."
    #                 job.job_status = ModelingJob.JobStatus.ERROR
    #                 job.save()
    #             else:
    #                 job.job_status = ModelingJob.JobStatus.DONE
    #                 job.save()
    #     else:
    #         job.error_message = "No labeling job reference error."
    #         job.job_status = ModelingJob.JobStatus.ERROR
    #         job.save()
    job = get_progress_api(pk=pk)

    response_data = {
        'state': job.job_status,
        'details': job.error_message if job.job_status == ModelingJob.JobStatus.ERROR else job.job_status,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')


class TermWeightUpdate(LoginRequiredMixin, generic.UpdateView):
    model = TermWeight
    form_class = TermWeightForm
    template_name = 'term_weights/update_form.html'


class TermWeightCreate(LoginRequiredMixin, generic.CreateView):
    form_class = TermWeightForm
    template_name = 'term_weights/add_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['modeling_job'] = self.kwargs.get('job_id')
        return kwargs

    def form_valid(self, form):
        form.instance.modeling_job_id = self.kwargs.get('job_id')
        return super(TermWeightCreate, self).form_valid(form)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('modeling_jobs:job-detail', kwargs={"pk": job_id})


class TermWeightDelete(LoginRequiredMixin, generic.DeleteView):
    model = TermWeight
    # success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'term_weights/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            logger.debug(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(TermWeightDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        job_id = self.kwargs.get('pk')
        return reverse_lazy('modeling_job_id:job-detail', kwargs={"pk": job_id})


class UploadModelJobCreate(LoginRequiredMixin, generic.CreateView):
    model = UploadModelJob
    form_class = UploadModelJobForm
    template_name = 'model_upload/file_upload_form.html'

    def get_success_url(self):
        # 利用django-q實作非同步上傳
        a = AsyncTask(import_model_data_task, upload_job=self.object, group='upload_model')
        a.run()
        job_id = self.kwargs['job_id']
        return reverse_lazy('modeling_jobs:job-detail', kwargs={'pk': job_id})

    def form_valid(self, form):
        logger.debug(self.kwargs)
        form.instance.modeling_job_id = self.kwargs.get('job_id')
        form.instance.created_by = self.request.user
        logger.debug(form.instance)
        return super(UploadModelJobCreate, self).form_valid(form)


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
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        logger.debug(self.basename)
        job_id = self.request.query_params.get('job')
        if job_id is not None:
            return TermWeight.objects.filter(modeling_job_id=job_id).order_by('-weight')
        else:
            return TermWeight.objects.all().order_by('-weight')
