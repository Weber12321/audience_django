from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory, inlineformset_factory, modelformset_factory
from django.http import HttpResponseRedirect
# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from predicting_jobs.forms import PredictingJobForm, TargetFormSet, PredictingTargetForm
from predicting_jobs.models import PredictingJob, PredictingTarget


class IndexView(LoginRequiredMixin, generic.ListView):
    queryset = PredictingJob.objects.order_by('-created_at')
    template_name = "predicting_jobs/index.html"
    context_object_name = 'predicting_jobs'


class PredictingJobDetailView(LoginRequiredMixin, generic.DetailView):
    model = PredictingJob
    context_object_name = 'predicting_job'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'predicting_jobs/predicting_job_detail.html'


class PredictingJobCreate(LoginRequiredMixin, generic.CreateView):
    form_class = PredictingJobForm
    template_name = 'predicting_jobs/predicting_job_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PredictingJobUpdate(LoginRequiredMixin, generic.UpdateView):
    model = PredictingJob
    form_class = PredictingJobForm
    template_name = 'predicting_jobs/predicting_job_form.html'


class PredictingJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = PredictingJob
    success_url = reverse_lazy('predicting_jobs:index')

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            print(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(PredictingJobDelete, self).post(request, *args, **kwargs)


class PredictingTargetUpdate(LoginRequiredMixin, generic.UpdateView):
    model = PredictingTarget
    form_class = PredictingTargetForm
    template_name = 'predicting_jobs/target_update.html'


class PredictingTargetCreate(LoginRequiredMixin, generic.CreateView):
    form_class = PredictingTargetForm
    template_name = 'predicting_jobs/target_add.html'

    def form_valid(self, form):
        form.instance.predicting_job_id = self.kwargs.get('job_id')
        return super(PredictingTargetCreate, self).form_valid(form)
