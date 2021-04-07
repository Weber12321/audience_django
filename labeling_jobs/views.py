import re
from random import shuffle

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import SingleObjectMixin
from django_q.tasks import AsyncTask

from .forms import LabelingJobForm, UploadFileJobForm, LabelForm
from .models import LabelingJob, UploadFileJob, Document, Label

# Create your views here.
from .tasks import import_csv_data_task


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

    def get_success_url(self):
        return reverse_lazy('labeling_jobs:index')


class LabelingJobUpdate(LoginRequiredMixin, generic.UpdateView):
    model = LabelingJob
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/labeling_job_form.html'

    def get_success_url(self):
        _pk = self.kwargs['pk']
        return reverse_lazy('labeling_jobs:job-detail', kwargs={'pk': _pk})


class LabelingJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = LabelingJob
    success_url = reverse_lazy('labeling_jobs:index')
    template_name = 'labeling_jobs/labeling_job_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            print(request.POST)
            return HttpResponseRedirect(self.success_url)
        else:
            return super(LabelingJobDelete, self).post(request, *args, **kwargs)


class LabelingJobDocumentsView(SingleObjectMixin, generic.ListView):
    paginate_by = 10
    model = LabelingJob

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'labeling_jobs/document_list.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=LabelingJob.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['labeling_job'] = self.object
        return context

    def get_queryset(self):
        return self.object.document_set.order_by('pk')


class LabelingRandomDocumentView(SingleObjectMixin, generic.ListView):
    paginate_by = 1
    model = LabelingJob
    template_name = 'labeling_jobs/labeling_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=LabelingJob.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['labeling_job'] = self.object
        return context

    def get_queryset(self):
        query_set = list(self.object.document_set.filter(labels=None))
        shuffle(query_set)
        return query_set if query_set else []


@csrf_exempt
def doc_label_update(request, job_id):
    doc_id = request.POST["doc-id"]
    label_ids = request.POST.getlist("label-ids")
    next_page = request.POST.get("next", None)
    labels = [Label.objects.get(pk=label_id) for label_id in label_ids]
    doc = Document.objects.get(id=doc_id)
    doc.labels.clear()
    for label in labels:
        doc.labels.add(label)
    doc.save()
    if next_page:
        return HttpResponseRedirect(next_page)
    else:
        return HttpResponseRedirect(reverse('labeling_jobs:job-labeling', kwargs={'pk': job_id}))


class UploadFileJobCreate(LoginRequiredMixin, generic.CreateView):
    model = UploadFileJob
    form_class = UploadFileJobForm
    template_name = 'labeling_jobs/file_upload_form.html'

    def get_success_url(self):
        from labeling_jobs.tasks import sample_task
        # 利用django-q實作非同步上傳
        a = AsyncTask(import_csv_data_task, self.object, group='upload_documents')
        a.run()
        job_id = self.kwargs['job_id']
        return reverse_lazy('labeling_jobs:job-detail', kwargs={'pk': job_id})

    def form_valid(self, form):
        form.instance.labeling_job_id = self.kwargs.get('job_id')
        form.instance.created_by = self.request.user
        return super(UploadFileJobCreate, self).form_valid(form)


class UploadFileJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = UploadFileJob
    success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'labeling_jobs/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            print(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(UploadFileJobDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": job_id})


class LabelUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Label
    form_class = LabelForm
    template_name = 'labels/update_form.html'


class LabelCreate(LoginRequiredMixin, generic.CreateView):
    # model = PredictingTarget
    form_class = LabelForm
    template_name = 'labels/add_form.html'

    def form_valid(self, form):
        form.instance.labeling_job_id = self.kwargs.get('job_id')
        return super(LabelCreate, self).form_valid(form)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": job_id})


class LabelDelete(LoginRequiredMixin, generic.DeleteView):
    model = Label
    success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'labels/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            print(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(LabelDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": job_id})


class LabelDetail(SingleObjectMixin, generic.ListView):
    paginate_by = 10
    model = LabelingJob

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'labels/label_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Label.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['label'] = self.object
        return context

    def get_queryset(self):
        return self.object.document_set.order_by('pk')


class DocumentDetailView(LoginRequiredMixin, generic.DetailView):
    model = Document
    context_object_name = 'doc'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'documents/document_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            context['next'] = re.sub('^https?:\/\/[\w.:]+', '', referer)
        return context
