from collections import namedtuple
from datetime import datetime
from time import sleep
from typing import List, Dict, Iterable, Generator

from tqdm import tqdm

from core.audience.models.base_model import AudienceModel, DummyModel
from core.audience.audience_worker import AudienceWorker, RESULT
from core.dao.input_example import InputExample
from modeling_jobs.tasks import load_model
from predicting_jobs.models import PredictingJob, PredictingTarget, JobStatus, ApplyingModel, PredictingResult


class TaskCanceledByUser(Exception):
    pass


def get_dummy_predicting_target_data(predicting_target: PredictingTarget, ):
    for i in range(10000):
        yield InputExample(
            id_=f"WH_{i}",
            s_area_id=f"WH_{i}",
            author=predicting_target.name,
            title=predicting_target.name,
            content=predicting_target.description, post_time=datetime.now())


def get_models(applying_models: List[ApplyingModel]) -> List[AudienceModel]:
    model_list = []
    for applying_model in applying_models:
        model = load_model(applying_model.modeling_job)
        model.load()
        model_list.append(model)
        print(model.__str__())
    return model_list


def reset_predict_targets(job: PredictingJob, status=JobStatus.WAIT):
    for target in job.predictingtarget_set.all():
        target.job_status = JobStatus.WAIT
        target.save()


def check_if_status_break(job_id):
    job: PredictingJob = PredictingJob.objects.get(pk=job_id)
    status = job.job_status
    if isinstance(status, str):
        status = JobStatus(status)
    if status == JobStatus.BREAK:
        reset_predict_targets(job, status=JobStatus.BREAK)
        raise TaskCanceledByUser("Job canceled by user.")
    if status == JobStatus.ERROR:
        reset_predict_targets(job, status=JobStatus.BREAK)
        raise ValueError("Something happened or status changed by user.")


def predict_task(job: PredictingJob):
    chunks_size = 100
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
            check_if_status_break(job.id)
            print(f"Cleaning predicting data from target '{predicting_target}'")
            predicting_target.predictingresult_set.all().delete()
            predicting_target.save()
            predicting_target.job_status = JobStatus.PROCESSING
            predicting_target.save()
            input_examples: Iterable[InputExample] = get_dummy_predicting_target_data(predicting_target)
            for example_chunk in tqdm(chunks(input_examples, chunk_size=chunks_size)):
                sleep(1)
                check_if_status_break(job.id)
                batch_results = predict_worker.run_labeling(example_chunk)
                # todo save result tags into database
                for tmp_example, example_results in zip(example_chunk, batch_results):
                    ensemble_results: Dict[str, float] = predict_worker.ensemble_results(example_results,
                                                                                         bypass_same_label=True)
                    data_id = tmp_example.id_
                    for label_name, score in ensemble_results.items():
                        predicting_result = PredictingResult(predicting_target=predicting_target,
                                                             label_name=label_name,
                                                             score=score, data_id=data_id)
                        predicting_result.save()
            predicting_target.job_status = JobStatus.DONE
            predicting_target.save()

        # if success
        job.job_status = JobStatus.DONE
    except TaskCanceledByUser as e:
        job.job_status = JobStatus.BREAK
    except Exception as e:
        # if something wrong
        print(e)
        job.job_status = JobStatus.ERROR
    finally:
        job.save()


def chunks(generator, chunk_size):
    """Yield successive chunks from a generator"""
    chunk = []

    for item in generator:
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = [item]
        else:
            chunk.append(item)

    if chunk:
        yield chunk
