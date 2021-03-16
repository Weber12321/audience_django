from django.forms import modelformset_factory
from django.shortcuts import render, redirect
from django.views import generic
from django import forms

from .forms import JobForm
from .models import Job


# Create your views here.
class IndexView(generic.ListView):
    template_name = 'labeling_jobs/index.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return Job.objects.order_by('-created_at')


class JobDetailView(generic.DetailView):
    model = Job
    template_name = 'labeling_jobs/job_detail.html'


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
