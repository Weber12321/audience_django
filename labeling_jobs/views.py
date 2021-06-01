import os
import re
from random import shuffle

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404, HttpResponse, FileResponse
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import SingleObjectMixin
from django_q.tasks import AsyncTask

from .forms import LabelingJobForm, UploadFileJobForm, LabelForm, RuleForm, RegexForm
from .models import LabelingJob, UploadFileJob, Document, Label, Rule, SampleData
# Create your views here.
from .tasks import import_csv_data_task, generate_datasets_task


class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
    model = LabelingJob
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["labeling_jobs"] = self.model.objects.order_by('-created_at')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('labeling_jobs:index')


class LabelingJobDetailAndUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = LabelingJob
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/labeling_job_form.html'

    def get_success_url(self):
        _pk = self.kwargs['pk']
        return reverse_lazy('labeling_jobs:job-detail', kwargs={'pk': _pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["labeling_job"] = self.object

        # label form for modal
        label_form = LabelForm({'labeling_job': self.object.id, 'target_amount': 200})
        context["label_form"] = label_form

        # upload file form for modal
        upload_file_form = UploadFileJobForm({'labeling_job': self.object.id, })
        print(upload_file_form.fields)
        context["upload_file_form"] = upload_file_form

        # rule form for keyword rule job
        if self.object.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            rule_form = RuleForm({'labeling_job': self.object.id, 'score': 1})
            context["rule_form"] = rule_form

        # rule form for regex rule job
        if self.object.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            regex_form = RegexForm({'labeling_job': self.object.id})
            context["regex_form"] = regex_form

        return context

    def get_template_names(self):
        if self.object.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            return 'job_detail/keyword_job_detail.html'
        elif self.object.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            return 'job_detail/regex_job_detail.html'
        else:
            return 'job_detail/supervise_job_detail.html'


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
    object: LabelingJob
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
        return self.object.document_set.exclude(document_type=Document.TypeChoices.EXT_TEST).order_by('pk')


class LabelingRandomDocumentView(SingleObjectMixin, generic.ListView):
    object: LabelingJob
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
    for label in labels:
        doc.labels.add(label)
    doc.save()
    if next_page:
        return HttpResponseRedirect(next_page)
    else:
        return HttpResponseRedirect(reverse('labeling_jobs:job-labeling', kwargs={'pk': job_id}))


def generate_dataset(request, job_id):
    job = LabelingJob.objects.get(pk=job_id)
    a = AsyncTask(generate_datasets_task, job=job, group="generate_dataset")
    a.run()
    return HttpResponseRedirect(reverse('labeling_jobs:job-detail', kwargs={'pk': job_id}))


class UploadFileJobCreate(LoginRequiredMixin, generic.CreateView):
    model = UploadFileJob
    form_class = UploadFileJobForm
    template_name = 'labeling_jobs/file_upload_form.html'

    def get_success_url(self):
        # 利用django-q實作非同步上傳
        a = AsyncTask(import_csv_data_task, upload_job=self.object, group='upload_documents')
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

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        pk = self.kwargs.get('pk')
        # if self.object.labeling_job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
        return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": job_id})
        # else:
        #     return reverse_lazy('labeling_jobs:label-detail', kwargs={"job_id": job_id, "pk": pk})


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
    object: Label
    paginate_by = 10
    model = Label

    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'documents/label_document_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Label.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['label'] = self.object
        labeling_job = self.object.labeling_job
        # rule form for keyword rule job
        if labeling_job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            rule_form = RuleForm({'labeling_job': labeling_job.id, 'score': 1, 'label': self.object.id})
            context["rule_form"] = rule_form

        # rule form for regex rule job
        if labeling_job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            regex_form = RegexForm({'labeling_job': labeling_job.id, 'label': self.object.id})
            context["rule_form"] = regex_form
        return context

    def get_template_names(self):
        if self.object.labeling_job.job_data_type in {LabelingJob.DataTypes.RULE_BASE_MODEL,
                                                      LabelingJob.DataTypes.REGEX_MODEL}:
            return 'rules/label_rule_detail.html'
        else:
            return 'documents/label_document_detail.html'

    def get_queryset(self):
        if self.object.labeling_job.job_data_type in {LabelingJob.DataTypes.RULE_BASE_MODEL,
                                                      LabelingJob.DataTypes.REGEX_MODEL}:
            return self.object.rule_set.all()
        else:
            return self.object.document_set.order_by('pk')


class RuleUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Rule
    form_class = RuleForm
    template_name = 'rules/update_form.html'

    def get_form_class(self):
        if self.object.labeling_job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            return RegexForm
        else:
            return RuleForm


class RuleCreate(LoginRequiredMixin, generic.CreateView):
    form_class = RuleForm
    template_name = 'rules/add_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['labeling_job_id'] = self.kwargs.get('job_id')
        return kwargs

    # def post(self, request, *args, **kwargs):
    #     print(request.POST.getlist)
    #     super(RuleCreate, self).post(request)

    def get_form_class(self):
        job = LabelingJob.objects.get(pk=self.kwargs.get('job_id'))
        if job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            return RegexForm
        elif job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            return RuleForm
        else:
            raise ValueError(f"job {job} is not a rule-base job.")

    def get_initial(self):
        initial = super(RuleCreate, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['labeling_job'] = self.kwargs.get('job_id')
        label_id = self.kwargs.get("label_id")
        if label_id:
            initial['label'] = self.kwargs.get('label_id')
        return initial

    def form_valid(self, form):
        # print(form)
        form.instance.labeling_job_id = self.kwargs.get('job_id')
        return super(RuleCreate, self).form_valid(form)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        label_id = self.kwargs.get("label_id")
        if label_id:
            return reverse_lazy('labeling_jobs:label-detail', kwargs={"job_id": job_id, 'pk': label_id})
        else:
            return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": job_id})


class RuleDelete(LoginRequiredMixin, generic.DeleteView):
    model = Rule
    # success_url = reverse_lazy('predicting_jobs:index')
    template_name = 'rules/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            # print(request.POST)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(RuleDelete, self).post(request, *args, **kwargs)

    def get_success_url(self):
        label_id = self.object.label.id
        job_id = self.kwargs.get('job_id')
        return reverse_lazy('labeling_jobs:label-detail', kwargs={"job_id": job_id, 'pk': label_id})


class DocumentDetailView(LoginRequiredMixin, generic.DetailView):
    model = Document
    context_object_name = 'doc'
    # generic.DetailView use default template_name =  <app name>/<model name>_detail.html
    template_name = 'documents/document_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            context['next'] = re.sub(r'^https?://[\w.:]+', '', referer)
        return context


class SampleDataListView(LoginRequiredMixin, generic.ListView):
    model = SampleData
    template_name = 'sample_data/data_list.html'


def download_sample_data(request, sample_data_id):
    sample_data = SampleData.objects.get(pk=sample_data_id)
    file_path = sample_data.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        return response
    raise Http404
