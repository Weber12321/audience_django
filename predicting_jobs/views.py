import json
import logging
from typing import Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy
from django.views import generic
from django_q.tasks import async_task
from rest_framework import viewsets, permissions
from django_filters import filters
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend
from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet

from audience_toolkits.settings import MODEL_TYPE, PREDICT_TYPE, OUTPUT_DB
from predicting_jobs.forms import PredictingJobForm, PredictingTargetForm, ApplyingModelForm
from predicting_jobs.models import PredictingJob, PredictingTarget, ApplyingModel, PredictingResult, JobStatus
from predicting_jobs.serializers import JobSerializer, ResultSerializer, TargetSerializer, ApplyingModelSerializer
from predicting_jobs.tasks import predict_task, get_queued_tasks_dict, call_create_task, call_result_samples, \
    call_check_status, check_job_status, check_jobs_status, check_targets_status, call_abort_task, check_target_status, \
    call_delete_task

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
    model = PredictingJob
    queryset = PredictingJob.objects.order_by('-created_at')
    template_name = "index.html"
    context_object_name = 'predicting_jobs'
    form_class = PredictingJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["predicting_jobs"] = PredictingJob.objects.order_by('-created_at')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PredictingJobDetailAndUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = PredictingJob
    context_object_name = 'predicting_job'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'predicting_jobs/detail.html'
    form_class = PredictingJobForm


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["predicting_job"] = self.object
        apply_model_form = ApplyingModelForm({'predicting_job': self.object, 'priority': 0})
        context["apply_model_form"] = apply_model_form
        predicting_target_form = PredictingTargetForm(
            {'predicting_job': self.object, 'min_content_length': 10, 'max_content_length': 500})
        context["predicting_target_form"] = predicting_target_form
        return context

    def get_success_url(self):
        _pk = self.kwargs['pk']
        return reverse_lazy('predicting_jobs:job-detail', kwargs={'pk': _pk})



class PredictingJobCreate(LoginRequiredMixin, generic.CreateView):
    form_class = PredictingJobForm
    template_name = 'predicting_jobs/add_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PredictingJobUpdate(LoginRequiredMixin, generic.UpdateView):
    model = PredictingJob
    form_class = PredictingJobForm
    template_name = 'predicting_jobs/update_form.html'

    def get_success_url(self):
        pk = self.kwargs.get("pk")
        return reverse_lazy('predicting_jobs:job-detail', kwargs={"pk": pk})


class PredictingJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = PredictingJob
    success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'predicting_jobs/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            logger.debug(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(PredictingJobDelete, self).post(request, *args, **kwargs)


class PredictingTargetUpdate(LoginRequiredMixin, generic.UpdateView):
    model = PredictingTarget
    form_class = PredictingTargetForm
    template_name = 'predicting_target/update_form.html'


class PredictingTargetCreate(LoginRequiredMixin, generic.CreateView):
    # model = PredictingTarget
    form_class = PredictingTargetForm
    template_name = 'predicting_target/add_form.html'

    def form_valid(self, form):
        form.instance.predicting_job_id = self.kwargs.get('job_id')
        return super(PredictingTargetCreate, self).form_valid(form)


class PredictingTargetDelete(LoginRequiredMixin, generic.DeleteView):
    model = PredictingTarget
    success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'predicting_target/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        self.success_url = reverse_lazy('predicting_jobs:job-detail', kwargs={"pk": job_id})
        if "cancel" in request.POST:
            logger.debug(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(PredictingTargetDelete, self).post(request, *args, **kwargs)


class ApplyingModelUpdate(LoginRequiredMixin, generic.UpdateView):
    model = ApplyingModel
    form_class = ApplyingModelForm
    template_name = 'predicting_target/update_form.html'


class ApplyingModelCreate(LoginRequiredMixin, generic.CreateView):
    model = ApplyingModel
    form_class = ApplyingModelForm
    template_name = 'predicting_target/add_form.html'

    def form_valid(self, form):
        form.instance.predicting_job_id = self.kwargs.get('job_id')
        try:
            return super(ApplyingModelCreate, self).form_valid(form)
        except IntegrityError as e:
            form.add_error('modeling_job', error="應用模型任務不能重複，請檢查目前已新增的任務。")
            return super(ApplyingModelCreate, self).form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form))


class ApplyingModelDelete(LoginRequiredMixin, generic.DeleteView):
    model = ApplyingModel
    success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'applying_model/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            logger.debug(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(ApplyingModelDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('predicting_jobs:job-detail', kwargs={"pk": job_id})


class PredictResultSamplingListView(LoginRequiredMixin, generic.ListView):
    paginate_by = 25
    model = PredictingResult
    template_name = "predicting_target/predict_result.html"
    context_object_name = 'result_rows'

    # def get_queryset(self):
    #     label_name = self.request.GET.dict().get("label_name")
    #     # if label_name:
    #     #     return PredictingResult.objects.filter(predicting_target=self.kwargs.get('pk'), label_name=label_name)
    #     # else:
    #     #     return PredictingResult.objects.filter(predicting_target=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        # label_name = self.request.GET.dict().get("label_name")
        context = super(PredictResultSamplingListView, self).get_context_data(**kwargs)
        # todo 待測試multi-label時的狀況
        # context['exist_labels'] = sorted(
        #     [labels[0] for labels in set(PredictingResult.objects.values_list("label_name"))])
        # context['current_label'] = label_name
        context['predicting_target'] = PredictingTarget.objects.get(pk=self.kwargs.get('pk'))
        context['predicting_job'] = PredictingJob.objects.get(pk=self.kwargs.get('job_id'))
        return context


def start_job(request, pk):
    if request.method == 'POST':
        target_id = request.GET.get('target_id', None)
        logger.info(request.POST)
        job = PredictingJob.objects.get(pk=pk)

        if target_id:
            target_set = [job.predictingtarget_set.get(pk=target_id)]
        else:
            target_set = job.predictingtarget_set.all()

        for target in target_set:
            target.job_status = JobStatus.WAIT
            target.error_message = ""
            target.save()

        logger.info(f'Predict targets: {[target.name for target in target_set]}')

        # queued_tasks: dict = get_queued_tasks_dict()
        for target in target_set:
            task_name = f"{job.name}-{target.name}"

            if target.task_id:
                logger.info(f'task is already exist...delete task {target.task_id} first')
                response_dict = call_delete_task(job=job, predicting_target=target)
                logger.info(f'{response_dict}')


            api_response: Dict = call_create_task(job, target, output_db=OUTPUT_DB)
            if not api_response:
                continue
            target.task_id = api_response['error_message']
            target.save()

            if api_response['error_code'] != 200:
                target.job_status = JobStatus.ERROR
                target.save()
                logger.warning(f"{task_name} with task_id {target.task_id} failed")
                logger.warning(f"task error_code {api_response['error_code']} "
                               f"with error_msg {api_response['error_message']}")



        return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:index"))
    return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:job-detail", kwargs={'pk': pk}))


def cancel_job(request, pk):
    if request.method == 'POST':
        target_id = request.GET.get('target_id', None)
        logger.info(request.POST)
        job = PredictingJob.objects.get(pk=pk)

        if target_id:
            target_set = [job.predictingtarget_set.get(pk=target_id)]
        else:
            target_set = job.predictingtarget_set.all()

        logger.info(f'Canceling targets: {[target.name for target in target_set]}')

        # queued_tasks: dict = get_queued_tasks_dict()
        for target in target_set:
            task_id = target.task_id
            # task = queued_tasks.get(task_id)
            # logger.debug(task)
            # if target.job_status != JobStatus.PROCESSING:
            #     return
            logger.info(f"Canceling job {target}...")
            call_abort_task(job, target)
            # target.job_status = JobStatus.BREAK
            target.error_message = "Canceled by user."
            # target.task_id = None
            target.save()

        return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:index"))
    return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:job-detail", kwargs={'pk': pk}))

def get_progress(request, pk):
    job = PredictingJob.objects.get(pk=pk)

    check_dict = {}
    targets = job.predictingtarget_set.all()
    target_task_id_list = [target.task_id for target in targets]
    if None in target_task_id_list:
        if sum(x is None for x in target_task_id_list) == len(targets):
            job.job_status = JobStatus.WAIT
            job.save()
        else:
            job.job_status = JobStatus.PROCESSING
            job.save()

            for target in targets:
                if not target.task_id:
                    continue
                if target.job_status == JobStatus.ERROR:
                    job.job_status = JobStatus.ERROR
                    job.save()

    for target in targets:
        if target.task_id:
            check_dict.update({
                target.task_id : check_target_status(target)
            })

    success_count = 0
    # if job.job_status == "processing":
    for t_id,t_response in check_dict.items():
        prod = t_response['error_message']['prod_stat']
        stat = t_response['error_message']['stat']
        if prod == 'no_data':
            success_count += 1
        if prod != 'finish':
            if stat == 'FAILURE':
                job.job_status = JobStatus.ERROR
                job.save()
            if stat == 'BREAK':
                continue
            if stat == 'PENDING':
                continue
        if prod == 'finish':
            success_count += 1


    if success_count == len(targets):
        job.job_status = JobStatus.DONE
        job.save()

    response_data = {
        'state': job.job_status,
        'details': check_dict,
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')


# rest api views

class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = PredictingJob.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplyingModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ApplyingModel.objects.all()
    serializer_class = ApplyingModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class TargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = PredictingTarget.objects.all()
    serializer_class = TargetSerializer
    permission_classes = [permissions.IsAuthenticated]


# django-filter datatable
class GlobalCharFilter(GlobalFilter, filters.CharFilter):
    pass


# django-filter datatable
class GlobalChoiceFilter(GlobalFilter, filters.ChoiceFilter):
    pass


class PredictingResultFilter(DatatablesFilterSet):
    """Filter name, artist and genre by name with icontains"""
    id = GlobalCharFilter(field_name='id', lookup_expr='icontains')
    applied_content = GlobalCharFilter(field_name='applied_content', lookup_expr='icontains')
    applied_feature = GlobalCharFilter(field_name='applied_feature', lookup_expr='icontains')
    label = GlobalCharFilter(field_name='label__name', lookup_expr='icontains')

    class Meta:
        model = PredictingResult
        fields = [
            'id',
            'source_author',
            'data_id',
            'label_name',
            'applied_model',
            'applied_feature',
            'applied_content',
            'created_at'
        ]


class ResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = PredictingResult.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (DatatablesFilterBackend,)
    filterset_class = PredictingResultFilter

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        target_id = self.request.query_params.get('target_id')
        source_author = self.request.query_params.get('source_author')
        logger.debug(target_id)
        query_set = PredictingResult.objects.all()
        if target_id:
            query_set = query_set.filter(predicting_target_id=target_id)
        if source_author:
            query_set = query_set.filter(source_author=source_author)

        return query_set.order_by('-created_at')


# =========================
#       Audience API
# =========================
import csv
def sample_download(request, pk):
    # Create the HttpResponse object with the appropriate CSV header.
    target = PredictingTarget.objects.get(pk=pk)
    sample_data: Dict = call_result_samples(target.task_id)

    if sample_data['error_code'] != 200:
        raise Http404(f'{sample_data["error_message"]}')

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="sample_results.csv"'},
    )

    fieldnames = list(sample_data['error_message'][0].keys())
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    for i in sample_data['error_message']:
        writer.writerow(i)

    return response

def render_sample_results(request, job_id, pk):
    target = PredictingTarget.objects.get(pk=pk)
    sample_data: Dict = call_result_samples(target.task_id)
    template = loader.get_template('predicting_target/sample_result.html')

    if sample_data['error_code'] != 200:
        context = {
            'error_message': "抽樣資料錯誤，錯誤訊息 :" + " " + sample_data['error_message']
        }
        return HttpResponse(template.render(context, request))
    else:
        context = {
            'sample_data' : sample_data['error_message']
        }
        return HttpResponse(template.render(context, request))

def render_status(request, job_id, pk):
    target = PredictingTarget.objects.get(pk=pk)
    template = loader.get_template('predicting_target/task_list.html')


    status_data = call_check_status(target.task_id)
    if status_data['error_code'] != 200:
        context = {
            'error': status_data['error_message'],
        }
        return HttpResponse(template.render(context, request))


    context = {
        'status' : status_data['error_message'],
    }
    return HttpResponse(template.render(context, request))


def render_all_status(request, pk):
    job = PredictingJob.objects.get(pk=pk)
    targets = job.predictingtarget_set.all()
    # template = loader.get_template('predicting_target/job_task_list.html')

    status = []
    for target in targets:

        if target.task_id:
            status_data = call_check_status(target.task_id)
        else:
            continue

        status.append(status_data['error_message'])

    return render(request, 'predicting_target/job_task_list.html', {'status':status})







