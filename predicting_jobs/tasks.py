from collections import namedtuple
from datetime import datetime
from typing import List, Dict

from core.audience.models.base_model import AudienceModel, DummyModel
from core.audience.audience_worker import AudienceWorker, RESULT
from core.dao.input_example import InputExample
from predicting_jobs.models import PredictingJob, PredictingTarget, JobStatus, ApplyingModel, PredictingResult


def get_dummy_predicting_target_data(predicting_target: PredictingTarget):
    return [
        InputExample(
            id_=f"WH_{i}",
            s_area_id=f"WH_{i}",
            author=predicting_target.name,
            title=predicting_target.name,
            content=predicting_target.description, post_time=datetime.now())
        for i in range(10)
    ]


def get_models(applying_models: List[ApplyingModel]) -> List[AudienceModel]:
    model_list = []
    for applying_model in applying_models:
        model = DummyModel(applying_model.modeling_job.name)
        model_list.append(model)
    return model_list


def get_dummy_models(num=2):
    return [DummyModel(dummy_message=f"I'm number {i}") for i in range(num)]


def get_dummy_label_set():
    DummyLabel = namedtuple("Label", "name, id")
    label1 = DummyLabel(name="dummy_label 1", id=1)
    label2 = DummyLabel(name="dummy_label 2", id=2)
    label3 = DummyLabel(name="dummy_label 3", id=2)
    return [label1, label2]


def get_dummy_modeling_jobs(num=2):
    DummyJobRef = namedtuple("LabelingJob", "label_set")
    modeling_job = namedtuple("ModelingJob", "jobRef")
    DummyLabelSet = namedtuple("LabelSet", "all")
    label_set = DummyLabelSet(all=get_dummy_label_set)
    job_ref = DummyJobRef(label_set=label_set)
    return [modeling_job(jobRef=job_ref) for i in range(num)]


def predict_task(job: PredictingJob):
    job.job_status = JobStatus.PROCESSING
    job.save()

    # models = get_models(job.applyingmodel_set.order_by("priority", "created_at"))
    models = get_dummy_models(num=3)
    predict_worker = AudienceWorker(models)
    # modeling_jobs = [model.modeling_job for model in job.applyingmodel_set.all()]
    modeling_jobs = get_dummy_modeling_jobs(2)
    # start predicting
    for predicting_target in job.predictingtarget_set.all():
        print(f"Cleaning predicting data from target '{predicting_target}'")
        predicting_target.predictingresult_set.all().delete()
        predicting_target.save()
        try:
            predicting_target.job_status = JobStatus.PROCESSING
            predicting_target.save()
            input_examples: List[InputExample] = get_dummy_predicting_target_data(predicting_target)
            for i, results in enumerate(predict_worker.run(input_examples)):
                # todo save result tags into database
                tmp_results = []
                bypass_label_set = set()
                for modeling_job, result in zip(modeling_jobs, results):
                    # get all label and id mapping for create predicting_result
                    label_id_mapping = {label.name: label.id for label in modeling_job.jobRef.label_set.all()}
                    _results = []
                    for rs in result:
                        if rs.label not in bypass_label_set:
                            _result = RESULT(label_id_mapping.get(rs.label, rs.label), rs.score)
                            if not isinstance(_result.label, int):
                                bypass_label_set.add(_result.label)
                                print(f"[ERROR] Unknown Label '{rs.label}' in {modeling_job}, pass")
                            else:
                                _results.append(_result)
                    tmp_results.append(_results)
                ensemble_results: Dict[str, float] = predict_worker.ensemble_results(tmp_results,
                                                                                     bypass_same_label=True)
                data_id = input_examples[i].id_
                for label_id, score in ensemble_results.items():
                    predicting_result = PredictingResult(predicting_target=predicting_target, label_id=label_id,
                                                         score=score, data_id=data_id)
                    predicting_result.save()
            predicting_target.job_status = JobStatus.DONE
            predicting_target.save()
        except Exception as e:
            # if something wrong
            print(e.with_traceback())
            job.job_status = JobStatus.ERROR
            job.save()
    # if success
    job.job_status = JobStatus.DONE
    job.save()
