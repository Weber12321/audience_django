import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import generic
from django_q.tasks import AsyncTask
from rest_framework import viewsets, permissions, filters

from predicting_jobs.forms import PredictingJobForm, PredictingTargetForm, ApplyingModelForm
from predicting_jobs.models import PredictingJob, PredictingTarget, ApplyingModel, PredictingResult
from predicting_jobs.serializers import JobSerializer, ResultSerializer, TargetSerializer, ApplyingModelSerializer
from predicting_jobs.tasks import predict_task

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

    def get_queryset(self):
        label_name = self.request.GET.dict().get("label_name")
        if label_name:
            return PredictingResult.objects.filter(predicting_target=self.kwargs.get('pk'), label_name=label_name)
        else:
            return PredictingResult.objects.filter(predicting_target=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        label_name = self.request.GET.dict().get("label_name")
        context = super(PredictResultSamplingListView, self).get_context_data(**kwargs)
        # todo 待測試multi-label時的狀況
        context['exist_labels'] = sorted(
            [labels[0] for labels in set(PredictingResult.objects.values_list("label_name"))])
        context['current_label'] = label_name
        context['predicting_target'] = PredictingTarget.objects.get(pk=self.kwargs.get('pk'))
        context['predicting_job'] = PredictingJob.objects.get(pk=self.kwargs.get('job_id'))
        return context


def start_job(request, pk):
    if request.method == 'POST':
        logger.debug("start predicting")
        target_id = request.POST.get('target_id', None)
        job = PredictingJob.objects.get(pk=pk)
        if target_id:
            logger.info(f'Predict target {PredictingTarget.objects.get(pk=target_id)}')
            target = PredictingTarget.objects.get(pk=target_id)
            a = AsyncTask(predict_task, job=job, predicting_target=target, group="predicting_audience")
            a.run()
        else:
            logger.info(f'Predict all targets: {[target.name for target in job.predictingtarget_set.all()]}')
            jobs = [AsyncTask(predict_task, job=job, predicting_target=target, group="predicting_audience") for target
                    in job.predictingtarget_set.all()]
            for j in jobs:
                j.run()
        return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:index"))
    return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:job-detail", kwargs={'pk': pk}))


def get_progress(request, pk):
    job = PredictingJob.objects.get(pk=pk)
    response_data = {
        'state': job.job_status,
        'details': {target.id: {"status": target.get_job_status_display(),
                                "sa_count": target.get_group_by_source_author().count()} for target in
                    job.predictingtarget_set.all()},
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


class ResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = PredictingResult.objects.all().order_by('-created_at')
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    # filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    # search_fields = "__all__"

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        target_id = self.request.query_params.get('target_id')
        logger.debug(target_id)
        if target_id:
            return PredictingResult.objects.filter(predicting_target_id=target_id).order_by('-created_at')
        else:
            return PredictingResult.objects.all().order_by('-created_at')
