import json
import logging
from collections import defaultdict
from itertools import groupby
from pathlib import PurePath, Path
from typing import Optional

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


def call_document_update(task_id: str, name: str, description: str,
                         task_type: str, is_multi_label: bool):
    try:
        api_path = f"{API_PATH}/documents/{task_id}/update"
        api_headers = API_HEADERS
        request_data = {
            "NAME": name,
            "DESCRIPTION": description,
            "TASK_TYPE": task_type,
            "IS_MULTI_LABEL": "true" if is_multi_label else "false"
        }
        response = requests.patch(
            url=api_path,
            headers=api_headers,
            data=json.dumps(request_data)
        )
        return response
    except Exception as e:
        raise e


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


def call_dataset_upload(task_id: str, overwrite: bool, file):
    try:
        bool_string = "true" if overwrite else "false"
        api_path = f"{API_PATH}/documents/{task_id}/upload?overwrite={bool_string}"
        api_headers = API_HEADERS
        response = requests.post(
            url=api_path,
            headers=api_headers,
            files={'file': file}
        )
        return response
    except Exception as e:
        raise e


def call_data_retrieve(dataset_id: int):
    try:
        api_path = f"{API_PATH}/documents/dataset/{dataset_id}"
        api_headers = API_HEADERS
        response = requests.get(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def call_rule_retrieve(rule_id: int):
    try:
        api_path = f"{API_PATH}/documents/rules/{rule_id}"
        api_headers = API_HEADERS
        response = requests.get(
            url=api_path,
            headers=api_headers
        )
        return response

    except Exception as e:
        raise e


def call_data_update(dataset_id: int, title: Optional[str], author: Optional[str],
                     content: str, dataset_type: str):
    try:
        api_path = f"{API_PATH}/documents/dataset/{dataset_id}/update"
        api_headers = API_HEADERS
        request_data = {
            "TITLE": title,
            "AUTHOR": author,
            "CONTENT": content,
            "DATASET_TYPE": dataset_type
        }
        response = requests.patch(
            url=api_path,
            headers=api_headers,
            data=json.dumps(request_data)
        )
        return response
    except Exception as e:
        raise e


def call_rule_add(task_id: str, content: str, label: str,
                  rule_type: str, match_type: str):
    try:
        api_path = f"{API_PATH}/documents/{task_id}/rules/add"
        api_headers = API_HEADERS
        request_data = {
            "CONTENT": content,
            "LABEL": label,
            "RULE_TYPE": rule_type,
            "MATCH_TYPE": match_type
        }
        response = requests.post(
            url=api_path,
            headers=api_headers,
            data=json.dumps(request_data)
        )
        return response

    except Exception as e:
        raise e


def call_rule_update(rule_id: int, content: str, label: str, rule_type: str, match_type: str):
    try:
        api_path = f"{API_PATH}/documents/rules/{rule_id}/update"
        api_headers = API_HEADERS
        request_data = {
            "CONTENT": content,
            "LABEL": label,
            "RULE_TYPE": rule_type,
            "MATCH_TYPE": match_type
        }
        response = requests.patch(
            url=api_path,
            headers=api_headers,
            data=json.dumps(request_data)
        )
        return response

    except Exception as e:
        raise e


def call_data_delete(dataset_id: int):
    try:
        api_path = f"{API_PATH}/documents/dataset/{dataset_id}/delete"
        api_headers = API_HEADERS
        response = requests.delete(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def call_rule_delete(rule_id: int):
    try:
        api_path = f"{API_PATH}/documents/rules/{rule_id}/delete"
        api_headers = API_HEADERS
        response = requests.delete(
            url=api_path,
            headers=api_headers
        )
        return response
    except Exception as e:
        raise e


def create_details_dir():
    root_dir = PurePath(__file__).parent
    folder = "dataset_details"
    save_detail_folder = Path(root_dir / folder)
    Path(save_detail_folder).mkdir(exist_ok=True)
    return save_detail_folder


def create_sample_dir():
    root_dir = PurePath(__file__).parent
    folder = "sample_file"
    save_sample_folder = Path(root_dir / folder)
    Path(save_sample_folder).mkdir(exist_ok=True)
    return save_sample_folder


def dataset_stats(task_id: str):
    task = call_get_task(task_id=task_id)
    task_type = task.json().get('task_type')
    dataset_response = call_dataset_render(task_id, task_type)
    stats = {}
    if task_type == 'rule_task':
        content_list = [data.get('content') for data in dataset_response.json()]

        stats.update({
            'length': len(content_list),
        })
    elif task_type == 'machine_learning_task':
        sorted_dataset = sorted(dataset_response.json(), key=key_func)
        for k, v in groupby(sorted_dataset, key_func):
            stats.update({
                k: {
                    'length': len(list(v)),
                    }
            })
    else:
        raise ValueError(f"task {task_id} unknown task type {task_type}")

    return stats


def key_func(dicts, group_key='dataset_type'):
    return dicts[group_key]
