from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from .forms import LabelingJobForm, LabelForm
from .models import LabelingJob, Label


# Create your views here.
class IndexView(LoginRequiredMixin, generic.ListView):
    queryset = LabelingJob.objects.order_by('-created_at')
    # generic.ListView use default template_name = '<app name>/<model name>_list.html'
    template_name = 'labeling_jobs/index.html'
    context_object_name = 'labeling_jobs'
    # def get_queryset(self):
    #     return Job.objects.order_by('-created_at')


class LabelingJobDetailView(LoginRequiredMixin, generic.DetailView):
    model = LabelingJob
    context_object_name = 'labeling_job'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'labeling_jobs/labeling_job_detail.html'


class LabelingJobCreate(LoginRequiredMixin, generic.CreateView):
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/labeling_job_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class LabelingJobUpdate(LoginRequiredMixin, generic.UpdateView):
    model = LabelingJob
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/labeling_job_form.html'


class LabelingJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = LabelingJob
    success_url = reverse_lazy('labeling_jobs:index')

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return HttpResponseRedirect(self.success_url)
        else:
            return super(LabelingJobDelete, self).post(request, *args, **kwargs)


class LabelingJobDocumentsView(SingleObjectMixin, generic.ListView):
    paginate_by = 2
    model = LabelingJob

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    # template_name = 'labeling_jobs/labeling_job_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=LabelingJob.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['labeling_job'] = self.object
        return context

    def get_queryset(self):
        return self.object.document_set.all()
