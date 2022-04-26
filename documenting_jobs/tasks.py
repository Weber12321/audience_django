import json
import logging
from pathlib import PurePath, Path

import requests

from audience_toolkits.settings import API_PATH, API_HEADERS
from documenting_jobs.models import DocumentingJob


def call_render_tasks():
    api_path = f"{API_PATH}/documents/"
    api_headers = API_HEADERS
    response = requests.get(url=api_path, headers=api_headers)
    return response


def call_get_task(task_id: str):
    api_path = f"{API_PATH}/documents/{task_id}"
    api_headers = API_HEADERS
    response = requests.get(url=api_path, headers=api_headers)
    return response


def call_task_create(task_id: str, **kwargs):
    try:
        api_path = f"{API_PATH}/documents/{task_id}/add"
        api_headers = API_HEADERS
        request_data = {
            'NAME': kwargs.get('name', None),
            'DESCRIPTION': kwargs.get('description', None),
            'TASK_TYPE': kwargs.get('task_type', None),
            'IS_MULTI_LABEL': kwargs.get('is_multi_label', False)
        }
        response = requests.post(
            url=api_path,
            headers=api_headers,
            data=json.dumps(request_data)
        )
        return response
    except Exception as e:
        raise e


def call_task_delete(task_id: str):
    try:
        api_path = f"{API_PATH}/documents/{task_id}/delete"
        api_headers = API_HEADERS
        response = requests.delete(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def call_document_update(job: DocumentingJob):
    pass


def call_dataset_render(task_id: str, task_type: str):
    try:
        if task_type == 'rule_task':
            api_path = f"{API_PATH}/documents/{task_id}/rules"
        elif task_type == 'machine_learning_task':
            api_path = f"{API_PATH}/documents/{task_id}/dataset"
        else:
            raise ValueError(f"Unknown task_type {task_type}")
        api_headers = API_HEADERS
        response = requests.get(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def call_post_download(task_id: str):
    try:
        api_path = f"{API_PATH}/documents/{task_id}/download"
        api_headers = API_HEADERS
        response = requests.post(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def call_get_download(task_id: str):
    api_path = f"{API_PATH}/documents/{task_id}/download"
    api_headers = API_HEADERS
    response = requests.get(
        url=api_path,
        headers=api_headers
    )
    detail_folder_path = create_details_dir()
    file_path = Path(detail_folder_path / f'{task_id}_doc.csv')
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path


def create_details_dir():
    root_dir = PurePath(__file__).parent
    folder = "dataset_details"
    save_detail_folder = Path(root_dir / folder)
    Path(save_detail_folder).mkdir(exist_ok=True)
    return save_detail_folder
