import json
from datetime import datetime
from time import sleep
from typing import List, Dict, Iterable

from django.utils import timezone
from tqdm import tqdm

from audience_toolkits import settings
from core.audience.audience_worker import AudienceWorker
from core.audience.models.base_model import SuperviseModel
from core.dao.input_example import InputExample
from core.helpers.data_helpers import chunks, get_opview_data_rows
from modeling_jobs.tasks import get_model
from predicting_jobs.models import PredictingJob, PredictingTarget, JobStatus, ApplyingModel, PredictingResult, Source


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
        model_list.append(model)
        # print(model.__str__())
    return model_list


def reset_predict_targets(job: PredictingJob, status=JobStatus.WAIT):
    for target in job.predictingtarget_set.all():
        target.job_status = status
        target.save()


def check_if_status_break(job_id):
    job: PredictingJob = PredictingJob.objects.get(pk=job_id)
    status = job.job_status
    if isinstance(status, str):
        status = JobStatus(status)
    if status == JobStatus.BREAK:
        reset_predict_targets(job, status=JobStatus.BREAK)
        raise TaskCanceledByUserException("Job canceled by user.")
    if status == JobStatus.ERROR:
        reset_predict_targets(job, status=JobStatus.BREAK)
        raise ValueError("Something happened or status changed by user.")


def predict_task(job: PredictingJob):
    batch_size = 1000
    job.job_status = JobStatus.PROCESSING
    job.save()
    reset_predict_targets(job)
    applying_models = job.applyingmodel_set.order_by("priority", "created_at")
    models = get_models(applying_models)
    predict_worker = AudienceWorker(models)
    modeling_jobs = [applying_model.modeling_job for applying_model in applying_models]
    print(f"Using models:", [mj.name for mj in modeling_jobs])
    # start predicting
    try:
        for predicting_target in job.predictingtarget_set.all():
            document_count = 0
            check_if_status_break(job.id)
            print(f"Cleaning predicting data from target '{predicting_target}'")
            predicting_target.predictingresult_set.all().delete()
            predicting_target.job_status = JobStatus.PROCESSING
            predicting_target.save()
            input_examples: Iterable[InputExample] = get_target_data(predicting_target, fetch_size=batch_size,
                                                                     max_rows=10000,
                                                                     max_len=int(predicting_target.max_content_length),
                                                                     min_len=int(predicting_target.min_content_length))
            for example_chunk in tqdm(chunks(input_examples, chunk_size=batch_size),
                                      desc=f'{batch_size} documents per iter'):
                # sleep(1)
                check_if_status_break(job.id)
                batch_results = predict_worker.run_labeling(example_chunk)
                # todo save result tags into database
                for tmp_example, example_results in zip(example_chunk, batch_results):
                    document_count += 1
                    ensemble_results, apply_path = predict_worker.ensemble_results(example_results,
                                                                                   bypass_same_label=True)
                    data_id = tmp_example.id_
                    for label_name, score in ensemble_results.items():
                        predicting_result = PredictingResult(
                            predicting_target=predicting_target,
                            label_name=label_name,
                            score=score, data_id=data_id,
                            source_author=f"{tmp_example.s_id}_{tmp_example.author}",
                            apply_path=json.dumps(apply_path[label_name], ensure_ascii=False),
                            created_at=timezone.now()
                        )
                        # print(apply_path[label_name])
                        # print(label_name, tmp_example.content[:50], "..." if len(tmp_example.content) > 50 else "")
                        predicting_result.save()
                        # print(predicting_result.apply_path)
            print(f"target: {predicting_target.name} processed {document_count} documents.")
            predicting_target.job_status = JobStatus.DONE
            predicting_target.save()

        # if success
        job.job_status = JobStatus.DONE
    except TaskCanceledByUserException as e:
        job.error_message = "Job canceled by user."
        job.job_status = JobStatus.BREAK
    except Exception as e:
        # if something wrong
        print(e)
        job.error_message = e
        job.job_status = JobStatus.ERROR
    finally:
        job.save()

# todo 貼標結果抽驗
# 各標籤抽驗
# 抽驗結果下載
