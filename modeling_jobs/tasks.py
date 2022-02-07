import json
import logging
from collections import defaultdict, namedtuple
from typing import List, Union, Dict, Tuple

import numpy as np
import requests
from django.db.models import QuerySet
from sklearn import preprocessing

from audience_toolkits import settings
from audience_toolkits.settings import API_HEADERS, API_PATH
from core.audience.models.base_model import SuperviseModel, RuleBaseModel
from core.audience.models.classic.term_weight_model import TermWeightModel
from core.dao.input_example import Features, InputExample
from core.helpers.model_helpers import get_model_class
from labeling_jobs.models import Document, LabelingJob, Label
from labeling_jobs.tasks import create_documents, read_csv_file
from modeling_jobs.models import ModelingJob, UploadModelJob

# Get an instance of a logger
logger = logging.getLogger(__name__)
TERM_WEIGHT_FIELDS_MAPPING = {
    'content': '字詞',
    'label': '標籤',
    'score': '分數',
}


def import_model_data_task(upload_job: UploadModelJob):
    upload_job.job_status = UploadModelJob.JobStatus.PROCESSING
    upload_job.save()
    try:
        file = upload_job.file
        logger.debug(upload_job.modeling_job.model_name)
        if upload_job.modeling_job.model_name in {"TERM_WEIGHT_MODEL"}:
            import_term_weights(file, upload_job.modeling_job, normalize_score=True,
                                required_fields=TERM_WEIGHT_FIELDS_MAPPING)
        else:
            raise ValueError(f'Unknown or unsupported model {upload_job.modeling_job.model_name}.')
        upload_job.job_status = UploadModelJob.JobStatus.DONE
    except Exception as e:
        logger.debug(e)
        upload_job.job_status = UploadModelJob.JobStatus.ERROR
    finally:
        upload_job.save()


def import_term_weights(file, job: ModelingJob, required_fields=None, normalize_score=True):
    if not required_fields:
        required_fields = TERM_WEIGHT_FIELDS_MAPPING
    label_term_weight: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    csv_rows = read_csv_file(file, required_fields)

    for index, row in enumerate(csv_rows):
        data = defaultdict(str)
        for _field in required_fields.keys():
            # 判斷欄位是否有出現在可使用的欄位名稱列表中
            field_data = row.get(_field, None) or row.get(required_fields.get(_field), None)
            if _field == 'score':
                field_data = field_data if field_data else 1
            data[_field] = field_data
        label_str: str = data.get('label', None)
        content = data.get('content', None)
        score = data.get('score', 1)
        label_term_weight[label_str].append((content, score))
    if normalize_score:
        normalized_label_term_weight = {}
        for label, term_weight in label_term_weight.items():
            terms, weights = [[i for i, j in term_weight],
                              [j for i, j in term_weight]]
            weights = np.array(weights)
            weights = weights.reshape(-1, 1)
            min_max_scaler = preprocessing.MinMaxScaler()
            weights_minmax = min_max_scaler.fit_transform(weights)
            weights_minmax = [round(weight[0], 6) for weight in weights_minmax]
            normalized_label_term_weight[label] = [t_w for t_w in zip(terms, weights_minmax)]
        label_term_weight = normalized_label_term_weight
    create_term_weights(job=job, label_term_weight=label_term_weight, reset_term_weights=False)


def train_model_task(job: ModelingJob):
    job.job_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        model_path = f"{job.id}_{job.name}"
        model = get_model(job, model_path, for_training=True, na_tag='一般')
        if isinstance(model, SuperviseModel):
            train_set = job.jobRef.get_train_set()
            contents, y_true = get_examples_and_labels(train_set)
            job.model_path = model.fit(examples=contents, y_true=y_true)

            if isinstance(model, TermWeightModel):
                create_term_weights(job, model.label_term_weights)
            # get train set report
            eval_dataset(model=model, dataset_type=Document.TypeChoices.TRAIN, dataset=train_set, job=job)
        elif isinstance(model, RuleBaseModel):
            raise ValueError(f"{model.__class__.__name__} is not trainable.")

        # get dev set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.DEV, dataset=job.jobRef.get_dev_set(), job=job)

        # get test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.TEST, dataset=job.jobRef.get_test_set(), job=job)

        job.job_status = ModelingJob.JobStatus.DONE
        job.save()
        logger.debug('training done')

    except Exception as e:
        logger.debug(e)
        job.error_message = e
        job.job_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def testing_model_via_ext_data_task(uploaded_file, job: ModelingJob, remove_old_data=True):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        create_ext_data(uploaded_file=uploaded_file, job=job.jobRef, remove_old_data=remove_old_data)
        logger.debug(job.model_name, job.model_path, job.is_multi_label)
        model = get_model(job)
        if isinstance(model, TermWeightModel):
            model.load(get_term_weights(job))
        # get ext test set report
        eval_dataset(model=model, dataset_type=Document.TypeChoices.EXT_TEST, dataset=job.jobRef.get_ext_test_set(),
                     job=job)
        job.ext_test_status = ModelingJob.JobStatus.DONE
        logger.debug('test done')
    except Exception as e:
        logger.debug(e)
        job.error_message = e
        job.ext_test_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def get_examples_and_labels(documents: List[Document]):
    examples: List[InputExample] = []
    labels = []
    for doc in documents:
        example = InputExample(id_=str(doc.id), s_id=doc.s_id, s_area_id=doc.s_area_id, title=doc.title,
                               author=doc.author,
                               content=doc.content,
                               post_time=doc.post_time)
        examples.append(example)
        labels.append([label.name for label in doc.labels.all()])
    return examples, labels


def create_ext_data(job: LabelingJob, uploaded_file, remove_old_data=True):
    if remove_old_data:
        job.document_set.filter(document_type=Document.TypeChoices.EXT_TEST).delete()
        job.save()
    create_documents(uploaded_file, job=job, document_type=Document.TypeChoices.EXT_TEST)


def get_model(job: ModelingJob, model_path=None, for_training=False, na_tag=None):
    if job.model_name in settings.ML_MODELS:
        model_cls = get_model_class(job.model_name)
        if not model_path and job.model_path is None or job.model_path == "":
            model_path = f"{job.id}_{job.name}"
        else:
            model_path = job.model_path
        logger.debug(f"======= {model_path} =======")
        model: Union[SuperviseModel, RuleBaseModel] = model_cls(
            model_dir_name=model_path,
            feature=Features(job.feature), na_tag=na_tag)
        if hasattr(model, 'is_multi_label'):
            # logger.debug(job.is_multi_label)
            model.is_multi_label = job.is_multi_label
        if isinstance(model, TermWeightModel):
            label_term_weights = get_term_weights(job)
            model.load(label_term_weights=label_term_weights)
        elif isinstance(model, SuperviseModel) and not for_training:
            model.load()
        elif isinstance(model, RuleBaseModel):
            rules = get_rules(job=job.jobRef)
            model.load(rules)
        return model
    else:
        raise ValueError(f"Unknown model: {job.model_name}")


def get_rules(job: LabelingJob):
    rules = defaultdict(list)
    for rule in job.rule_set.all():
        rules[rule.label.name].append((rule.content, rule.match_type))
    return rules


def create_term_weights(job: ModelingJob, label_term_weight: Dict[str, List[Tuple[str, float]]],
                        reset_term_weights=True):
    if reset_term_weights:
        job.termweight_set.all().delete()
    if not job.jobRef:
        job.jobRef = LabelingJob(name=f"「{job.name}」自動建立的任務",
                                 description=f"因「{job.name}」匯入而自動建立的任務",
                                 job_data_type=LabelingJob.DataTypes.TERM_WEIGHT_MODEL,
                                 created_by=job.created_by)
        job.jobRef.save()
        for label_str in label_term_weight.keys():
            job.jobRef.label_set.create(name=label_str)
        job.jobRef.save()
    label_dict = job.jobRef.get_labels_dict()
    for label_str, term_weights in label_term_weight.items():
        for term, weight in term_weights:
            if label_str not in label_dict:
                job.jobRef.label_set.create(name=label_str)
                job.save()
                label_dict = job.jobRef.get_labels_dict()
            try:
                job.termweight_set.create(term=term, weight=weight, label=label_dict.get(label_str))
                job.save()
            except Exception as e:
                logger.debug(e)
                logger.debug(term)
    job.save()


def get_term_weights(job: ModelingJob) -> Dict[str, List[Tuple[str, float]]]:
    label_term_weight: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for term_weight in job.termweight_set.all():
        label_term_weight[term_weight.label.name].append((term_weight.term, float(term_weight.weight),))
    return label_term_weight


def eval_dataset(model, job: ModelingJob, dataset, dataset_type: Document.TypeChoices):
    examples, y_true = get_examples_and_labels(dataset)
    report = model.eval(examples, y_true=y_true)
    logger.debug(report)
    report_json = json.dumps(report, ensure_ascii=False)
    tmp_report = job.report_set.create(dataset_type=dataset_type, report=report_json,
                                       accuracy=report.get('accuracy', -1))

    predict_labels, predict_logits = model.predict(examples)
    labels = {_label.name: _label for _label in job.jobRef.label_set.all()}
    logger.debug(labels)
    for doc, pred in zip(dataset, predict_labels):
        # process prediction
        pr = tmp_report.evalprediction_set.create(document=doc)
        if isinstance(pred, QuerySet):
            for _pred in pred:
                pr.prediction_labels.add(_pred)
        elif isinstance(pred, List):
            for _pred in pred:
                if isinstance(_pred, str):
                    pr_label = labels.get(_pred)
                    pr.prediction_labels.add(pr_label)
                    # logger.debug(pr)
                if isinstance(_pred, Label):
                    pr.prediction_labels.add(_pred)
        elif isinstance(pred, str):
            pr_label = labels.get(pred)
            pr.prediction_labels.add(pr_label)
        elif isinstance(pred, Label):
            pr.prediction_labels.add(labels.get(pred))
        else:
            raise ValueError(f"Unknown prediction data format {type(pred)}")
        pr.save()


# ===================================
#           Modeling API
# ===================================
def call_model_preparing(job: ModelingJob):
    job.job_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        model_path = f"{job.id}_{job.model_name}"
        api_path = f'{API_PATH}/models/prepare/'
        api_headers = API_HEADERS
        api_request_body = {"QUEUE": "queue2",
                            "DATASET_DB": "audience-toolkit-django",
                            "DATASET_NO": job.jobRef.id,
                            "TASK_ID": job.task_id.hex,
                            "PREDICT_TYPE": job.feature.upper(),
                            "MODEL_TYPE": job.model_name.upper(),
                            "MODEL_INFO": {"model_path": model_path,
                                           "feature_model": "SGD"
                                           }
                            }

        result = requests.post(url=api_path, headers=api_headers, data=json.dumps(api_request_body))

        if result.status_code != 200:
            logger.debug(result.json())
            job.error_message = result.json()
            job.job_status = ModelingJob.JobStatus.ERROR
            job.save()

    except Exception as e:
        logger.debug(e)
        job.error_message = e
        job.job_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def call_model_testing(uploaded_file, job: ModelingJob, remove_old_data=True):
    job.job_test_status = ModelingJob.JobStatus.PROCESSING
    job.save()
    try:
        create_ext_data(uploaded_file=uploaded_file, job=job.jobRef, remove_old_data=remove_old_data)
        logger.debug(job.model_name, job.model_path, job.is_multi_label)

        model_path = f"{job.id}_{job.model_name}"
        api_path = f'{API_PATH}/models/test/'
        api_headers = API_HEADERS
        api_request_body = {"QUEUE": "queue2",
                            "DATASET_DB": "audience-toolkit-django",
                            "DATASET_NO": job.jobRef.id,
                            "MODEL_JOB_ID": job.id,
                            "PREDICT_TYPE": job.feature.upper(),
                            "MODEL_TYPE": job.model_name.upper(),
                            "MODEL_INFO": {"model_path": model_path,
                                           "feature_model": "SGD"
                                           }
                            }
        result = requests.post(url=api_path, headers=api_headers, data=json.dumps(api_request_body))

        if isinstance(result.json(), str):
            logger.debug(f'Task is failed, since {result.json()}')
            job.error_message = result.json()
            job.ext_test_status = ModelingJob.JobStatus.ERROR
            job.save()

    except Exception as e:
        logger.debug(e)
        job.error_message = e
        job.ext_test_status = ModelingJob.JobStatus.ERROR
        job.save()
        raise ValueError("Task Failed")


def call_model_status(task_id: str):
    api_path = f"{API_PATH}/models/{task_id}"
    api_headers = API_HEADERS
    result = requests.get(url=api_path, headers=api_headers)
    return result.status_code, result.json()


def call_import_model_status(task_id: str, upload_job_id: int):
    api_path = f"{API_PATH}/models/{task_id}/import_model/{upload_job_id}"
    api_headers = API_HEADERS
    result = requests.get(url=api_path, headers=api_headers)
    return result.status_code, result.json()


def call_model_report(task_id: str):
    api_path = f"{API_PATH}/models/{task_id}/report/"
    api_headers = API_HEADERS
    report = requests.get(url=api_path, headers=api_headers)
    return report.status_code, report.json()


def process_report(task_id: str):
    status_code, report = call_model_report(task_id=task_id)
    reports: dict = _process_report(report)
    accuracy = reports.pop('accuracy')
    macro_avg = reports.pop('macro avg')
    macro_avg['f1_score'] = macro_avg['f1-score']
    weighted_avg = reports.pop('weighted avg')
    weighted_avg['f1_score'] = weighted_avg['f1-score']
    label_info = namedtuple('label_info', ['label', 'precision', 'recall', 'f1_score', 'support'])
    labels = []
    for key in reports.keys():
        label = reports.get(key)
        s = label_info(key, label.get('precision'), label.get('recall'), label.get('f1-score'), label.get('support'))
        labels.append(s)
    return {"accuracy": accuracy,
            "macro_avg": macro_avg,
            "weighted_avg": weighted_avg,
            "labels": labels}


def _process_report(report: dict):
    for key in report.keys():
        if key != 'accuracy':
            for i in report[key]:
                report[key][i] = round(report[key][i], 3)

    return report


def get_progress_api(pk):
    job = ModelingJob.objects.get(pk=pk)
    status_code, status_result = call_model_status(task_id=job.task_id.hex)
    if status_code == 200:
        if status_result['training_status'] in ('finished', 'untrainable'):
            job.job_status = ModelingJob.JobStatus.DONE
            job.save()
        elif status_result['training_status'] in ('pending', 'started'):
            job.job_status = ModelingJob.JobStatus.PROCESSING
            job.save()
        elif status_result['training_status'] == 'failed':
            job.job_status = ModelingJob.JobStatus.ERROR
            job.save()
        elif status_result['training_status'] == 'break':
            job.job_status = ModelingJob.JobStatus.BREAK
            job.save()
        else:
            job.job_status = ModelingJob.JobStatus.WAIT
            job.save()
        if status_result['ext_status']:
            if status_result['ext_status'] == 'finished':
                job.job_status = ModelingJob.JobStatus.DONE
                job.save()
            elif status_result['ext_status'] in ('pending', 'started'):
                job.job_status = ModelingJob.JobStatus.PROCESSING
                job.save()
            elif status_result['ext_status'] == 'failed':
                job.job_status = ModelingJob.JobStatus.ERROR
                job.save()
            elif status_result['ext_status'] == 'break':
                job.job_status = ModelingJob.JobStatus.BREAK
                job.save()
            else:
                job.job_status = ModelingJob.JobStatus.WAIT
                job.save()
    else:
        job.error_message = status_result
        job.job_status = ModelingJob.JobStatus.ERROR
        job.save()

    upload_set = ModelingJob.objects.filter(uploadmodeljob__modeling_job_id__exact=pk).values_list('uploadmodeljob__id','task_id')

    for upload_job_id, task_id in upload_set:
        _status_code, _status_result = call_import_model_status(task_id=task_id,
                                                                upload_job_id=upload_job_id)

        upload_job = UploadModelJob.objects.get(pk=upload_job_id)

        if _status_code == 200:
            if _status_result['status'] == 'finished':
                upload_job.job_status = UploadModelJob.JobStatus.DONE
                upload_job.save()
            if _status_result['status'] == 'failed':
                upload_job.job_status = UploadModelJob.JobStatus.ERROR
                upload_job.save()
        else:
            upload_job.job_status = UploadModelJob.JobStatus.ERROR
            upload_job.save()

    return job


def call_model_import(upload_job: UploadModelJob):
    upload_job.job_status = UploadModelJob.JobStatus.PROCESSING
    upload_job.save()
    try:
        file = upload_job.file
        api_path = f'{API_PATH}/models/import_model/'
        api_headers = API_HEADERS.update({'Content-Type': 'multipart/form-data'})
        api_request_body = {"QUEUE": "queue2",
                            "TASK_ID": upload_job.modeling_job.task_id,
                            "UPLOAD_JOB_ID": upload_job.id}
        if upload_job.modeling_job.model_name in {"TERM_WEIGHT_MODEL"}:
            logger.debug(upload_job.modeling_job.model_name)
            r = requests.put(url=api_path,
                             headers=api_headers,
                             files={'file': open(file.path, 'rb')},
                             data=json.dumps(api_request_body))
            if r.status_code != 200:
                logger.debug(r.json())
                upload_job.job_status = UploadModelJob.JobStatus.ERROR
        else:
            raise ValueError(f'Unknown or unsupported model {upload_job.modeling_job.model_name}.')
    except Exception as e:
        logger.debug(e)
        upload_job.job_status = UploadModelJob.JobStatus.ERROR
    finally:
        upload_job.save()
