import logging
import os
import re
from random import shuffle

from django_filters import filters
from rest_framework import mixins
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404, FileResponse
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import SingleObjectMixin
from django_q.tasks import AsyncTask, async_task
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend
from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet

from audience_toolkits.settings import LABELING_JOB_INDEX_URL
from .forms import LabelingJobForm, UploadFileJobForm, LabelForm, RuleForm, RegexForm
from .models import LabelingJob, UploadFileJob, Document, Label, Rule, SampleData

from .serializers import LabelingJobSerializer, LabelSerializer, RuleSerializer, UploadFileJobSerializer, \
    DocumentSerializer
from .tasks import import_csv_data_task, generate_datasets_task

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
    model = LabelingJob
    form_class = LabelingJobForm
    template_name = 'labeling_jobs/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["labeling_jobs"] = self.model.objects.order_by('-created_at')
        context["api_url"] = LABELING_JOB_INDEX_URL
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

    # def get_form(self, form_class=None):


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
        async_task(import_csv_data_task, upload_job=self.object, group='upload_documents')
        job_id = self.kwargs['job_id']
        return reverse_lazy('labeling_jobs:job-detail', kwargs={'pk': job_id})

    def form_valid(self, form):
        form.instance.job_id = self.kwargs.get('job_id')
        form.instance.created_by = self.request.user
        return super(UploadFileJobCreate, self).form_valid(form)


class UploadFileJobDelete(LoginRequiredMixin, generic.DeleteView):
    model = UploadFileJob
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
        job_id = self.kwargs.get('pk')
        # if self.object.labeling_job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
        return reverse_lazy('labeling_jobs:labels-detail', kwargs={"pk": job_id})
        # else:
        #     return reverse_lazy('labeling_jobs:label-detail', kwargs={"job_id": job_id, "pk": pk})


class LabelCreate(LoginRequiredMixin, generic.CreateView):
    form_class = LabelForm
    template_name = 'labels/add_form.html'

    def form_valid(self, form):
        form.instance.job_id = self.kwargs.get('job_id')
        return super(LabelCreate, self).form_valid(form)

    def get_success_url(self):
        job_id = self.kwargs.get('job_id')
        print(job_id)
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
        job_id = self.kwargs.get('pk')
        return reverse_lazy('labeling_jobs:job-detail', kwargs={"pk": self.object.labeling_job.id})


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
        job = self.object.labeling_job
        # rule form for keyword rule job
        if job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            rule_form = RuleForm(initial={'labeling_job': job.id, 'score': 1, 'label': self.object.id})
            context["rule_form"] = rule_form

        # rule form for regex rule job
        if job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            regex_form = RegexForm(initial={'labeling_job': job.id, 'label': self.object.id})
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

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs['job_id'] = self.kwargs.get('job_id')
    #     return kwargs

    def get_form_class(self):
        label_id = self.kwargs.get('label_id', None)
        if not label_id:
            label_id = self.request.POST.get('label')
        label = Label.objects.get(pk=label_id)
        if label.labeling_job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            return RegexForm
        elif label.labeling_job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            return RuleForm
        else:
            return RegexForm
            # raise ValueError(f"job {label.labeling_job} is not a rule-base job.")

    #
    # def get_initial(self):
    #     initial = super(RuleCreate, self).get_initial()
    #     # Copy the dictionary so we don't accidentally change a mutable dict
    #     initial = initial.copy()
    #     job_id = self.kwargs.get('job_id')
    #     if job_id:
    #         initial['labeling_job'] = self.kwargs.get('job_id')
    #     label_id = self.kwargs.get("label_id")
    #     if label_id:
    #         initial['label'] = self.kwargs.get('label_id')
    #     return initial

    def form_valid(self, form):
        # label_id = self.kwargs.get('label_id')
        # label = Label.objects.get(pk=label_id)
        # form.instance.label = label
        # form.instance.labeling_job = label.labeling_job
        form.instance.created_by = self.request.user
        rule_content = form.instance.content
        if Label.objects.get(pk=form.instance.label_id).rule_set.filter(content=rule_content).exists():
            form.add_error('content', "此規則已存在")
            return self.form_invalid(form)
        return super(RuleCreate, self).form_valid(form)

    def get_success_url(self):
        # label_id = self.kwargs.get("label_id")
        # if not label_id:
        label_id = self.object.label.id

        return reverse_lazy('labeling_jobs:labels-detail', kwargs={"pk": label_id})


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
        rule_id = self.kwargs.get('pk')
        rule = Rule.objects.get(pk=rule_id)
        return reverse_lazy('labeling_jobs:labels-detail', kwargs={'pk': rule.label_id})


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
    paginate_by = 10
    model = SampleData
    template_name = 'sample_data/data_list.html'

    def get_context_data(self, **kwargs):
        data_type = self.request.GET.dict().get("data_type")
        context = super().get_context_data(**kwargs)
        context['current_data_type'] = data_type
        context['data_types'] = [d_type for d_type in LabelingJob.DataTypes]
        print([d_type for d_type in LabelingJob.DataTypes])
        return context

    def get_queryset(self):
        data_type = self.request.GET.dict().get("data_type")
        if data_type:
            return SampleData.objects.filter(job_data_type=data_type)
        else:
            return SampleData.objects.all()


def download_sample_data(request, sample_data_id):
    sample_data = SampleData.objects.get(pk=sample_data_id)
    file_path = sample_data.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=sample_data.get_file_name())
        return response
    logger.error(f"File '{file_path}' missing.")
    raise Http404


# django-filter datatable
class GlobalCharFilter(GlobalFilter, filters.CharFilter):
    pass


class RuleFilter(DatatablesFilterSet):
    """Filter name, artist and genre by name with icontains"""
    id = GlobalCharFilter(field_name='id', lookup_expr='icontains')
    content = GlobalCharFilter(field_name='content', lookup_expr='icontains')
    label = GlobalCharFilter(field_name='label__name', lookup_expr='icontains')
    # todo: 目前只能篩選choice name("start"、"end"、"exactly"、"partially") => display_name("比對開頭"...)
    match_type_display = GlobalCharFilter(field_name="match_type", lookup_expr='icontains')

    class Meta:
        model = Rule
        fields = "__all__"


# rest api views

class LabelingJobsSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = LabelingJob.objects.all().order_by("-created_at")
    serializer_class = LabelingJobSerializer

    # def get_queryset(self):
    #     return LabelingJob.objects.all().order_by("-created_at")
    # permission_classes = [permissions.IsAuthenticated]


class LabelSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Label.objects.all().order_by("id")
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        labeling_job_id = self.request.GET.get('labeling_job')
        if labeling_job_id:
            return Label.objects.filter(labeling_job_id=labeling_job_id).order_by('id')
        else:
            return Label.objects.all().order_by('id')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        labeling_job_id = request.data['labeling_job_id']
        job = LabelingJob.objects.filter(id=labeling_job_id).first()
        serializer.save(job=job, )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RuleSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Rule.objects.all().order_by("id")
    serializer_class = RuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    # new: add SearchFilter and search_fields
    # https://django-rest-framework-datatables.readthedocs.io/en/latest/django-filters.html
    filter_backends = (DatatablesFilterBackend,)
    filterset_class = RuleFilter

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = LabelingJob.objects.get(pk=request.data["labeling_job_id"])
        label = Label.objects.get(pk=request.data["label_id"])
        serializer.save(labeling_job=job, label=label, created_by=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        labeling_job_id = self.request.GET.get('labeling_job')
        if labeling_job_id:
            return Rule.objects.filter(labeling_job_id=labeling_job_id).order_by('id')
        else:
            return Rule.objects.all().order_by('id')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        job = LabelingJob.objects.get(pk=request.data["job"])
        label = Label.objects.get(pk=request.data["label"])

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(labeling_job=job, label=label, created_by=instance.created_by)

        return Response(serializer.data)


class UploadFileJobSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                       mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = UploadFileJob.objects.all().order_by("id")
    serializer_class = UploadFileJobSerializer
    # permissions_classes = [permissions.IsAuthenticated]


class DocumentSet(viewsets.ModelViewSet):
    """
    Document CRUD API endpoint that allows users to be viewed.
    """
    queryset = Document.objects.all().order_by("id")
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        labeling_job_id = self.request.GET.get('labeling_job')
        if labeling_job_id:
            return Document.objects.filter(labeling_job_id=labeling_job_id).order_by('id')
        else:
            return Document.objects.all().order_by('id')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        labels = Label.objects.get(pk=request.data["label_id"])

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(labels=labels)

        return Response(serializer.data)
