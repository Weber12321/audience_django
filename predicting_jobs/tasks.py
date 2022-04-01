import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import List, Iterable, Dict, Optional

from django.utils import timezone
from django_q.models import OrmQ

from audience_toolkits import settings
from core.audience.audience_worker import AudienceWorker
from core.audience.models.base_model import SuperviseModel
from core.audience.models.classic.term_weight_model import TermWeightModel
from core.dao.input_example import InputExample
from core.helpers.data_helpers import chunks, get_opview_data_rows
from modeling_jobs.tasks import get_model, get_term_weights
from predicting_jobs.models import PredictingJob, PredictingTarget, JobStatus, ApplyingModel, PredictingResult, Source

# Get an instance of a logger
logger = logging.getLogger(__name__)


class TaskCanceledByUserException(Exception):
    pass


def get_dummy_predicting_target_data(predicting_target: PredictingTarget, ):
    for i in range(10000):
        yield InputExample(
            id_=f"WH_{i}",
            s_area_id=f"WH_{i}",
            author=predicting_target.name,
            title=predicting_target.name,
            content=predicting_target.description, post_time=datetime.now())


def get_target_data(predicting_target: PredictingTarget, fetch_size: int = 1000, max_rows: int = None,
                    fields=settings.AVAILABLE_FIELDS.keys(), min_len: int = 10, max_len: int = 1000):
    source: Source = predicting_target.source
    connection_settings = {
        "host": source.host,
        "port": source.port,
        "user": source.username,
        "password": source.password,
        "source_name": source.schema,
        "table": source.tablename,
        "fetch_size": fetch_size,
        "max_rows": max_rows,
        "fields": fields,
        "conditions": [
            f"post_time between '{predicting_target.begin_post_time}' and '{predicting_target.end_post_time}'"
        ]
    }
    for row in get_opview_data_rows(**connection_settings):
        if min_len <= len(row.get("content")) <= max_len:
            yield InputExample(
                id_=row.get("id"),
                s_id=row.get("s_id"),
                s_area_id=row.get("s_area_id"),
                author=row.get("author"),
                title=row.get("title"),
                content=row.get("content"),
                post_time=row.get("post_time"),
            )


def get_models(applying_models: List[ApplyingModel]) -> List[SuperviseModel]:
    model_list = []
    for applying_model in applying_models:
        model = get_model(applying_model.modeling_job)
        # print(model.model_dir_name)
        if isinstance(model, TermWeightModel):
            model.load(get_term_weights(applying_model.modeling_job))
        model_list.append(model)
        # print(model.__str__())
    return model_list


def reset_predict_targets(job: PredictingJob, status=JobStatus.WAIT):
    for target in job.predictingtarget_set.all():
        target.job_status = status
        target.save()


def check_if_status_break(target_id):
    target = PredictingTarget.objects.get(pk=target_id)
    status = target.job_status
    logger.debug(f"{target} is {target.job_status}.")
    if isinstance(status, str):
        status = JobStatus(status)
    if status == JobStatus.BREAK:
        # reset_predict_targets(job, status=JobStatus.BREAK)
        raise TaskCanceledByUserException("Job canceled by user.")
    if status == JobStatus.ERROR:
        # reset_predict_targets(job, status=JobStatus.BREAK)
        raise ValueError("Something happened or status changed by user.")


def predict_task(job: PredictingJob, predicting_target: PredictingTarget):
    batch_size = 1000
    job.job_status = JobStatus.PROCESSING
    job.save()
    # predicting_target.job_status = JobStatus.WAIT
    # predicting_target.save()
    applying_models = job.applyingmodel_set.order_by("priority", "created_at")
    models = get_models(applying_models)
    predict_worker = AudienceWorker(models)
    modeling_jobs = [applying_model.modeling_job for applying_model in applying_models]
    logger.info(f"Using models: {[mj.name for mj in modeling_jobs]}")
    # start predicting
    try:
        document_count = 0
        check_if_status_break(predicting_target.id)
        logger.debug(f"Cleaning predicting data from target '{predicting_target}'")
        predicting_target.predictingresult_set.all().delete()
        predicting_target.job_status = JobStatus.PROCESSING
        predicting_target.save()
        if settings.DEBUG:
            logger.warning("Debug mode, process will limit target data row (10000 rows).")
        input_examples: Iterable[InputExample] = get_target_data(predicting_target, fetch_size=batch_size,
                                                                 # max_rows=10000 if settings.DEBUG else None,
                                                                 max_len=int(predicting_target.max_content_length),
                                                                 min_len=int(predicting_target.min_content_length))
        for example_chunk in chunks(input_examples, chunk_size=batch_size):
            # sleep(1)
            check_if_status_break(predicting_target.id)
            batch_results = predict_worker.run_labeling(example_chunk)

            for tmp_example, example_results in zip(example_chunk, batch_results):
                document_count += 1
                # ensemble_results, apply_path = predict_worker.ensemble_results(example_results,
                #                                                                bypass_same_label=True)
                data_id = tmp_example.id_
                for result in example_results:
                    if not result.labels:
                        continue
                    for label in result.labels:
                        predicting_result = PredictingResult(
                            predicting_target=predicting_target,
                            label_name=label,
                            # score=score,
                            data_id=data_id,
                            source_author=f"{tmp_example.s_id}_{tmp_example.author}",
                            applied_model_id=int(result.model.split("_")[0]) if result.model else None,
                            applied_meta=result.logits.get(label) if hasattr(result.logits,
                                                                             "get") else result.logits,
                            applied_content=result.value,
                            applied_feature=result.feature,
                            created_at=timezone.now()
                        )
                        predicting_result.save()
                    # print(predicting_result.apply_path)
        logger.debug(f"target: {predicting_target.name} processed {document_count} documents.")
        predicting_target.job_status = JobStatus.DONE
        predicting_target.save()

        # if success
        job.job_status = JobStatus.DONE
    except TaskCanceledByUserException as e:
        job.error_message = "Job canceled by user."
        job.job_status = JobStatus.BREAK
    except Exception as e:
        # if something wrong
        logger.error(e)
        job.error_message = e
        job.job_status = JobStatus.ERROR
    finally:
        job.save()


# todo 貼標結果抽驗
# 各標籤抽驗
# 抽驗結果下載

def get_queued_tasks_id():
    return [t.task_id() for t in OrmQ.objects.all()]


def get_queued_tasks_dict():
    return {t.task_id(): t for t in OrmQ.objects.all()}


# =========================
#       Audience API
# =========================

import json
import requests
from audience_toolkits.settings import API_HEADERS, API_PATH


# create_task
def call_create_task(job: PredictingJob, predicting_target, output_db):
    applying_models = job.applyingmodel_set.order_by("priority", "created_at")

    job.job_status = JobStatus.PROCESSING
    job.save()

    source: Source = predicting_target.source

    if predicting_target.begin_post_time > predicting_target.end_post_time:
        predicting_target.job_status = JobStatus.ERROR
        predicting_target.save()
        return

    api_path = f'{API_PATH}/tasks/'

    api_headers = API_HEADERS

    # check if the model information is set in the backends, remove this method later
    check_model_record(applying_models=applying_models)

    task_id = predicting_target.task_id if predicting_target.task_id else uuid.uuid1().hex

    api_request_body = {
        "TASK_ID": task_id,
        "START_TIME": f"{predicting_target.begin_post_time}",
        "END_TIME": f"{predicting_target.end_post_time}",
        "INPUT_SCHEMA": source.schema,
        "INPUT_TABLE": source.tablename,
        "OUTPUT_SCHEMA": output_db,
        "COUNTDOWN": 5,
        "QUEUE": "queue1",
        "MODEL_ID_LIST": [apply_model.modeling_job.task_id.hex for apply_model in applying_models],
        "SITE_CONFIG": {"host": source.host,
                        "port": source.port,
                        "user": source.username,
                        "password": source.password,
                        'db': source.schema,
                        'charset': 'utf8mb4'}
    }

    try:
        predicting_target.job_status = JobStatus.PROCESSING
        predicting_target.save()

        r = requests.post(api_path, headers=api_headers, data=json.dumps(api_request_body))

        logger.info(f"HTTP status_code: {r.status_code}; response: {r.json()}")

        if r.status_code != 200:
            predicting_target.job_status = JobStatus.ERROR
            predicting_target.save()

        response_dict = r.json()
        return response_dict

    except Exception as e:
        # if something wrong
        logger.error(e)
        job.error_message = e
        job.job_status = JobStatus.ERROR

    finally:
        job.save()


# result_samples
def call_result_samples(task_id):
    sample_path = f'{API_PATH}/tasks/{task_id}/sample/'
    api_headers = {
        'accept': 'application/json',
    }

    r = requests.get(sample_path, headers=api_headers)

    sample_data: Optional[Dict] = r.json()

    return sample_data


# check_status
def call_check_status(task_id):
    check_status_path = f'{API_PATH}/tasks/{task_id}'
    api_headers = {
        'accept': 'application/json',
    }

    r = requests.get(check_status_path, headers=api_headers)

    if r.status_code != 200:
        return

    check_status_result = r.json()

    return check_status_result


# abort_task
def call_abort_task(job: PredictingJob, predicting_target: PredictingTarget):
    task_id = predicting_target.task_id

    if not task_id:
        return

    api_path = f'{API_PATH}/tasks/abort/'

    api_headers = API_HEADERS

    api_request_body = {
        "TASK_ID": task_id
    }

    try:
        r = requests.post(api_path, headers=api_headers, data=json.dumps(api_request_body))
        logger.info(f"HTTP status_code: {r.status_code}; response: {r.json()}")

        if r.status_code != 200:
            predicting_target.job_status = JobStatus.ERROR
            predicting_target.save()

        else:
            predicting_target.job_status = JobStatus.BREAK
            predicting_target.save()

        response_dict = r.json()
        return response_dict

    except Exception as e:
        # if something wrong
        logger.error(e)
        job.error_message = e
        job.job_status = JobStatus.ERROR
        job.save()


# delete_task
def call_delete_task(job: PredictingJob, predicting_target: PredictingTarget):
    task_id = predicting_target.task_id

    if not task_id:
        return

    api_path = f'{API_PATH}/tasks/delete/'

    api_headers = API_HEADERS

    api_request_body = {
        "TASK_ID": task_id
    }

    try:
        r = requests.post(api_path, headers=api_headers, data=json.dumps(api_request_body))
        logger.info(f"HTTP status_code: {r.status_code}; response: {r.json()}")

        if r.status_code != 200:
            predicting_target.job_status = JobStatus.ERROR
            predicting_target.save()

        else:
            predicting_target.job_status = JobStatus.WAIT
            predicting_target.save()

        response_dict = r.json()
        return response_dict

    except Exception as e:
        # if something wrong
        logger.error(e)
        job.error_message = e
        job.job_status = JobStatus.ERROR
        job.save()


def get_temp_rule(applying_models: List[ApplyingModel]) -> List[Dict]:
    model_list = []

    for applying_model in applying_models:
        if applying_model.modeling_job.model_name.lower() == 'regex_model':
            model = get_model(applying_model.modeling_job)
            if model.patterns:
                rule = dict(model.patterns)
                pattern = defaultdict(list)
                for k, v in rule.items():
                    for i in v:
                        pattern[k].append(i[0])
                model_list.append(dict(pattern))
        if applying_model.modeling_job.model_name.lower() == 'keyword_model':
            model = get_model(applying_model.modeling_job)
            if model.rules:
                model_list.append(dict(model.rules))

    return model_list


def check_job_status(job: PredictingJob):
    check_targets_status(job)
    targets = job.predictingtarget_set.all()

    try:
        for target in targets:
            if target.job_status == JobStatus.DONE:
                continue
            if target.job_status == JobStatus.PROCESSING:
                return
            if target.job_status == JobStatus.ERROR:
                job.status = JobStatus.ERROR
                job.save()
                return
            if target.job_status == JobStatus.BREAK:
                job.status = JobStatus.BREAK
                job.save()
                return
        job.status = JobStatus.DONE
        job.save()
    except Exception as e:
        job.status = JobStatus.ERROR
        job.save()


def check_jobs_status(jobs: List[PredictingJob]):
    for job in jobs:
        check_job_status(job)


def check_targets_status(job: PredictingJob):
    targets = job.predictingtarget_set.all()
    for target in targets:

        if target.job_status == JobStatus.PROCESSING:
            _result_dict = call_check_status(target.task_id)
            if isinstance(_result_dict['error_message'], Dict):
                if _result_dict['error_message']['prod_stat'] == 'finish':
                    target.job_status = JobStatus.DONE
                    target.save()
                if _result_dict['error_message']['stat'] == 'FAILURE':
                    target.job_status = JobStatus.ERROR
                    target.save()
            else:
                pass


def check_target_status(target: PredictingTarget):
    _result_dict = call_check_status(target.task_id)
    if isinstance(_result_dict['error_message'], Dict):
        if _result_dict['error_message']['prod_stat'] == 'finish':
            target.job_status = JobStatus.DONE
            target.save()
        if _result_dict['error_message']['prod_stat'] == 'no_data':
            target.job_status = JobStatus.DONE
            target.save()
        if _result_dict['error_message']['stat'] == 'FAILURE':
            target.job_status = JobStatus.ERROR
            target.save()
        if _result_dict['error_message']['stat'] == 'BREAK':
            target.job_status = JobStatus.BREAK
            target.save()
    else:
        pass

    return _result_dict


def check_model_record(applying_models):
    for applying_model in applying_models:
        r = requests.get(url=f"{API_PATH}/models/{applying_model.modeling_job.task_id.hex}")
        if r.status_code != 200:
            result = call_model_preparing(
                model_job_id=applying_model.modeling_job.task_id.hex,
                labeling_job_id=applying_model.modeling_job.jobRef.id,
                model_type=applying_model.modeling_job.model_name,
                feature=applying_model.modeling_job.feature.upper()
            )
            if result.status_code != 200:
                raise ValueError(f"cannot create a number due to {result.json()}")
        else:
            continue


def call_model_preparing(model_job_id: str, labeling_job_id: int, model_type: str, feature: str):
    api_path = f'{API_PATH}/models/prepare/'
    api_headers = API_HEADERS
    body = {
        "QUEUE": "queue2",
        "DATASET_DB": "audience-toolkit-django",
        "DATASET_NO": labeling_job_id,
        "MODEL_JOB_ID": model_job_id,
        "PREDICT_TYPE": feature,
        "MODEL_TYPE": model_type,
        "MODEL_INFO": {
            "model_path": f"{model_job_id}_{model_type}"
        }
    }
    r = requests.post(api_path, headers=api_headers, data=json.dumps(body))
    return r
