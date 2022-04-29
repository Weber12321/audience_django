import os
import uuid

from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from audience_toolkits.settings import DOCCANO_PATH
from documenting_jobs.forms import DocumentingJobForm, RulesUpdateForm, DatasetUpdateForm
from documenting_jobs.tasks import call_task_create, call_render_tasks, call_get_task, call_dataset_render, \
    call_post_download, call_get_download, call_task_delete, call_dataset_upload, call_data_retrieve, \
    call_rule_retrieve, call_rule_update, call_data_update, call_data_delete, call_rule_delete, call_document_update, \
    create_sample_dir, call_rule_add


# logger = logging.getLogger(__name__)

def render_index(request):
    template_name = "documenting_jobs/index.html"
    template = loader.get_template(template_name)
    form = DocumentingJobForm()
    response = call_render_tasks()
    context = {
        'documenting_jobs': response.json(),
        'form': form,
        'doccano': DOCCANO_PATH
    }
    return HttpResponse(template.render(context, request))


def render_detail(request, task_id):
    template_name = "job_details/dataset_detail.html"
    template = loader.get_template(template_name)
    task = call_get_task(task_id)
    task_type = task.json().get('task_type')
    dataset = call_dataset_render(task_id, task_type)
    context = {
        'job': task.json(),
        'dataset': dataset.json()
    }
    return HttpResponse(template.render(context, request))


def task_description(request, task_id):
    template_name = "documenting_jobs/description.html"
    template = loader.get_template(template_name)
    task = call_get_task(task_id)
    context = {
        'job': task.json()
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


@csrf_exempt
def task_update(request, task_id):
    template = loader.get_template('job_details/error_page.html')
    if request.method == 'POST':
        response = call_document_update(
            task_id=task_id,
            name=request.POST.get('task_name'),
            description=request.POST.get('task_description'),
            task_type=request.POST.get('task_task_type'),
            is_multi_label=request.POST.getlist('task_is_multi_label')
        )
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )
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


@csrf_exempt
def upload_file(request, task_id):
    template = loader.get_template('job_details/error_page.html')
    if request.method == 'POST':
        file = request.FILES.get('file')
        overwrite = request.POST.getlist('overwrite')
        response = call_dataset_upload(task_id, overwrite, file)
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )


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
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )


def get_download_file(request, task_id):
    file_path = call_get_download(task_id)
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = "application/vnd.ms-excel"
    response['Content-Disposition'] = f'attachment;filename="{task_id}_doc.csv"'
    return response


@csrf_exempt
def update_data(request, task_id, dataset_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_data_update(
            dataset_id=dataset_id,
            title=request.POST.get('title'),
            author=request.POST.get('author'),
            content=request.POST.get('content'),
            dataset_type=request.POST.get('dataset_type')
        )
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )

    template = loader.get_template('documenting_jobs/update_data.html')
    data = call_data_retrieve(dataset_id=dataset_id)
    context = {
        'task_id': task_id,
        'data': data.json()
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def add_rule(request, task_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_rule_add(
            task_id=task_id,
            content=request.POST.get('content'),
            label=request.POST.get('label'),
            rule_type=request.POST.get('rule_type'),
            match_type=request.POST.get('match_type')
        )
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )

    template = loader.get_template('documenting_jobs/update_rule.html')

    context = {
        'task_id': task_id
    }
    return HttpResponse(template.render(context, request))



@csrf_exempt
def update_rule(request, task_id, rule_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_rule_update(
            rule_id=rule_id,
            content=request.POST.get('content'),
            label=request.POST.get('label'),
            rule_type=request.POST.get('rule_type'),
            match_type=request.POST.get('match_type')
        )
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )

    template = loader.get_template('documenting_jobs/update_rule.html')
    data = call_rule_retrieve(rule_id=rule_id)
    context = {
        'task_id': task_id,
        'rule': data.json()
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def delete_data(request, task_id, dataset_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_data_delete(dataset_id=dataset_id)

        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))

        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )


@csrf_exempt
def delete_rule(request, task_id, rule_id):
    if request.method == 'POST':
        template = loader.get_template('job_details/error_page.html')
        response = call_rule_delete(rule_id=rule_id)
        if response.status_code != 200:
            context = {
                'error_code': response.status_code,
                'error_message': "錯誤訊息: " + f"{response.json()}"
            }
            return HttpResponse(template.render(context, request))
        return HttpResponseRedirect(
            reverse('documenting_jobs:job-detail', kwargs={"task_id": task_id})
        )


def download_sample_file(request):
    parent_dir = create_sample_dir()
    file_path = os.path.join(parent_dir,'sample.zip')
    response = FileResponse(open(file_path, 'rb'))
    return response
