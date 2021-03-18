from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from .models import Job


# Create your views here.
class IndexView(generic.ListView):
    queryset = Job.objects.order_by('-created_at')
    # generic.ListView use default template_name = '<app name>/<model name>_list.html'
    template_name = 'labeling_jobs/index.html'
    context_object_name = 'jobs'
    # def get_queryset(self):
    #     return Job.objects.order_by('-created_at')


class JobDetailView(generic.DetailView):
    model = Job
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    # template_name = 'labeling_jobs/job_detail.html'


class JobCreate(LoginRequiredMixin, generic.CreateView):
    model = Job
    fields = ['name', 'description', 'is_multi_label']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class JobUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Job
    fields = ['name', 'description']


class JobDelete(LoginRequiredMixin, generic.DeleteView):
    model = Job
    success_url = reverse_lazy('index')


class JobDocumentsView(SingleObjectMixin, generic.ListView):
    paginate_by = 2
    model = Job

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    # template_name = 'labeling_jobs/job_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Job.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object
        return context

    def get_queryset(self):
        return self.object.document_set.all()
