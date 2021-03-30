from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
# Create your views here.
from django.urls import reverse_lazy
from django.views import generic

from predicting_jobs.forms import PredictingJobForm, PredictingTargetForm, ApplyingModelForm
from predicting_jobs.models import PredictingJob, PredictingTarget, ApplyingModel


class IndexView(LoginRequiredMixin, generic.ListView):
    queryset = PredictingJob.objects.order_by('-created_at')
    template_name = "index.html"
    context_object_name = 'predicting_jobs'


class PredictingJobDetailView(LoginRequiredMixin, generic.DetailView):
    model = PredictingJob
    context_object_name = 'predicting_job'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'predicting_jobs/detail.html'


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
    # model = PredictingTarget
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
