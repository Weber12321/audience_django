import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from documenting_jobs.forms import DocumentingJobForm, RuleAddForm, RulesUpdateForm, DatasetUpdateForm
from documenting_jobs.models import DocumentingJob

logger = logging.getLogger(__name__)


class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
    model = DocumentingJob
    template_name = "documenting_jobs/index.html"
    form_class = DocumentingJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documenting_jobs'] = self.model.objects.order_by('-create_time')
        return context

    def form_valid(self, form):
        form.instance.create_time = self.request.user
        return super().form_valid(form)


class DetailAndUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = DocumentingJob
    form_class = DocumentingJobForm
    template_name = 'job_details/dataset_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job"] = self.object

        if self.object.job_type == 'rule_task':
            rules_create_form = RuleAddForm(initial={'task_id': self.object.task_id})
            rules_update_form = RulesUpdateForm(initial={'task_id': self.object.task_id})
            context['rules_create_form'] = rules_create_form
            context['rules_update_form'] = rules_update_form
        elif self.object.job_type == 'machine_learning_task':
            dataset_update_form = DatasetUpdateForm(initial={'task_id': self.object.task_id})
            context['dataset_update_form'] = dataset_update_form
        else:
            error_code = 400
            error_message = f"Unknown job type '{self.object.job_type}'"
            context['error_code'] = error_code
            context['error_message'] = error_message

        return context

    def get_template_names(self):
        logger.debug(self.object.job_type)
        if self.object.job_type == 'machine_learning_task':
            return 'job_details/dataset_detail.html'
        elif self.object.job_type == 'rule_task':
            return 'job_details/rules_detail.html'
        else:
            return 'job_details/error_page.html'

    def get_success_url(self):
        _pk = self.kwargs['pk']
        return reverse_lazy('documenting_jobs:dataset_detail.html', kwargs={'pk': _pk})


class JobCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = DocumentingJobForm
    template_name = 'documenting_jobs/add_form.html'

    def form_valid(self, form):
        form.instance.create_by = self.request.user
        return super().form_valid(form)


class JobDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = DocumentingJob
    success_url = reverse_lazy('documenting_jobs:index')
    template_name = 'documenting_jobs/confirm_delete_form.html'

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            logger.debug(request.POST)
            #TODO: add the delete api here
            return HttpResponseRedirect(self.success_url)
        else:
            return super(JobDeleteView, self).post(request, *args, **kwargs)


@csrf_exempt
def document_create(request, job_id):
    pass


@csrf_exempt
def document_update(request, job_id):
    pass


@csrf_exempt
def document_delete(request, job_id):
    pass


def document_render(request, job_id):
    pass


@csrf_exempt
def upload_file(request, job_id):
    pass


@csrf_exempt
def download_file(request, job_id):
    pass
