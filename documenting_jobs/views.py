import json
import logging
import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.template import loader
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from documenting_jobs.forms import DocumentingJobForm, RuleAddForm, RulesUpdateForm, DatasetUpdateForm
from documenting_jobs.models import DocumentingJob
from documenting_jobs.tasks import call_task_create, call_render_tasks, call_get_task, call_dataset_render, \
    call_post_download, call_get_download, call_task_delete

logger = logging.getLogger(__name__)


# class IndexAndCreateView(LoginRequiredMixin, generic.CreateView):
#     model = DocumentingJob
#     template_name = "documenting_jobs/index.html"
#     form_class = DocumentingJobForm
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['documenting_jobs'] = self.model.objects.order_by('-create_time')
#         return context
#
#     def form_valid(self, form):
#         form.instance.create_time = self.request.user
#         return super().form_valid(form)
#
#
# class DetailAndUpdateView(LoginRequiredMixin, generic.UpdateView):
#     model = DocumentingJob
#     form_class = DocumentingJobForm
#     template_name = 'job_details/dataset_detail.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["job"] = self.object
#
#         if self.object.job_type == 'rule_task':
#             rules_create_form = RuleAddForm(initial={'task_id': self.object.task_id})
#             rules_update_form = RulesUpdateForm(initial={'task_id': self.object.task_id})
#             context['rules_create_form'] = rules_create_form
#             context['rules_update_form'] = rules_update_form
#         elif self.object.job_type == 'machine_learning_task':
#             dataset_update_form = DatasetUpdateForm(initial={'task_id': self.object.task_id})
#             context['dataset_update_form'] = dataset_update_form
#         else:
#             error_code = 400
#             error_message = f"Unknown job type '{self.object.job_type}'"
#             context['error_code'] = error_code
#             context['error_message'] = error_message
#
#         return context
#
#     def get_template_names(self):
#         logger.debug(self.object.job_type)
#         if self.object.job_type == 'machine_learning_task':
#             return 'job_details/dataset_detail.html'
#         elif self.object.job_type == 'rule_task':
#             return 'job_details/rules_detail.html'
#         else:
#             return 'job_details/error_page.html'
#
#     def get_success_url(self):
#         _pk = self.kwargs['pk']
#         return reverse_lazy('documenting_jobs:dataset_detail.html', kwargs={'pk': _pk})
#
#
#
# class JobCreateView(LoginRequiredMixin, generic.CreateView):
#     form_class = DocumentingJobForm
#     template_name = 'documenting_jobs/add_form.html'
#
#     def form_valid(self, form):
#         form.instance.create_by = self.request.user
#         return super().form_valid(form)
#
#
# class JobDeleteView(LoginRequiredMixin, generic.DeleteView):
#     model = DocumentingJob
#     success_url = reverse_lazy('documenting_jobs:index')
#     template_name = 'documenting_jobs/confirm_delete_form.html'
#
#     def post(self, request, *args, **kwargs):
#         if "cancel" in request.POST:
#             logger.debug(request.POST)
#             #TODO: add the delete api here
#             return HttpResponseRedirect(self.success_url)
#         else:
#             return super(JobDeleteView, self).post(request, *args, **kwargs)

def render_index(request):
    template_name = "documenting_jobs/index.html"
    template = loader.get_template(template_name)
    form = DocumentingJobForm()
    response = call_render_tasks()
    context = {
        'documenting_jobs': response.json(),
        'form': form
    }
    return HttpResponse(template.render(context, request))


def task_create(request):
    if request.method == 'POST':
        form = DocumentingJobForm(
            request.POST
        )
        template = loader.get_template('job_details/error_page.html')
        if form.is_valid():
            task_id = uuid.uuid1().hex
            response = call_task_create(task_id=task_id, **form.cleaned_data)

            if response.status_code != 200:
                context = {
                    'error_code': response.status_code,
                    'error_message': "錯誤訊息: " + f"{response.json()}"
                }
                return HttpResponse(template.render(context, request))

            return HttpResponseRedirect(reverse('documenting_jobs:index'))


def render_detail(request, task_id):
    template_name = "job_details/dataset_detail.html"
    template = loader.get_template(template_name)
    task = call_get_task(task_id)
    task_type = task.json().get('task_type')
    dataset = call_dataset_render(task_id, task_type)
    context = {
        'jobs': task.json(),
        'dataset': dataset.json()
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def task_update(request, task_id):
    pass


@csrf_exempt
def task_delete(request, task_id):
    template = loader.get_template('job_details/error_page.html')
    response = call_task_delete(task_id)
    if response.status_code != 200:
        context = {
            'error_code': response.status_code,
            'error_message': "錯誤訊息: " + f"{response.json()}"
        }
        return HttpResponse(template.render(context, request))
    return HttpResponseRedirect(reverse('documenting_jobs:index'))


def task_render(request, task_id):
    pass


@csrf_exempt
def upload_file(request, task_id):
    pass


@csrf_exempt
def post_download_file(request, task_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_post_download(task_id)
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(reverse('documenting_jobs:job-detail'))


def get_download_file(request, task_id):
    file_path = call_get_download(task_id)
    response = FileResponse(open(file_path), 'rb')
    response['Content-Type'] = "application/vnd.ms-excel"
    response['Content-Disposition'] = f'attachment;filename="{task_id}_doc.csv"'
    return response


