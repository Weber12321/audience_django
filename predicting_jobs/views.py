from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
# Create your views here.
from django.urls import reverse_lazy
from django.views import generic
from django_q.tasks import AsyncTask

from predicting_jobs.forms import PredictingJobForm, PredictingTargetForm, ApplyingModelForm
from predicting_jobs.models import PredictingJob, PredictingTarget, ApplyingModel, PredictingResult
from predicting_jobs.tasks import predict_task
import json


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
            print(request.POST)
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
            print(request.POST)
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
            print(request.POST)
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
        print("start predicting")
        job = PredictingJob.objects.get(pk=pk)
        a = AsyncTask(predict_task, job, group="predicting_audience")
        a.run()
        return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:index"))
    return HttpResponseRedirect(redirect_to=reverse_lazy("predicting_jobs:job-detail", kwargs={'pk': pk}))


def get_progress(request, pk):
    job = PredictingJob.objects.get(pk=pk)

    response_data = {
        'state': job.job_status,
        'details': {target.name: target.job_status for target in job.predictingtarget_set.all()},
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')
