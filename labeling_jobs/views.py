from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic, View
from django import forms
from django.views.generic.detail import SingleObjectMixin

from .forms import JobForm
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


# class JobFormView(generic.FormView):
#     form_class = JobForm
#     initial = {"created_by": 1,
#                "name": "new job",
#                "description": "say something"}
#     template_name = "labeling_jobs/job_form.html"

# def get(self, request, *args, **kwargs):
#     form = self.form_class(initial=self.initial)
#     return render(request, self.template_name, {'form': form})
#
# def post(self, request):
#     form = self.form_class(request.POST)
#     if form.is_valid():
#         form.save()
#         return redirect('labeling_jobs:index')
#     return render(request, self.template_name, {'form': form})


def create_job(request):
    form = JobForm()
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('labeling_jobs:index')
    context = {
        'form': form
    }

    return render(request, 'labeling_jobs/job_edit.html', context=context)


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
