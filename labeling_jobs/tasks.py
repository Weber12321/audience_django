import codecs
import csv
import hashlib
from collections import defaultdict
from datetime import datetime
from random import shuffle
from time import sleep
from typing import List

import cchardet
from labeling_jobs.models import LabelingJob, Document, UploadFileJob, Label, Rule

# 以下的key都須與rule的欄位相同，才能比對的到資料
RULE_FIELDS_MAPPING = {
    'content': '字詞',
    'match_type': '判斷式',
    'label': '標籤',
    'score': '分數',
}

REGEX_FIELDS_MAPPING = {
    'content': '規則式',
    'label': '標籤',
}

# 以下的key都須與document的欄位相同，才能比對的到資料
DOCUMENT_FIELDS_MAPPING = {
    's_id': '來源',
    's_area_id': '來源網站',
    'title': '標題',
    'author': '作者',
    'content': '內容',
    'label': '標籤',
    'post_time': '發佈時間',
}


def sample_task(job: UploadFileJob, sleep_time=5):
    print(f'start doing job {job.file}')
    job.job_status = UploadFileJob.JobStatus.PROCESSING
    job.save()
    # your code here
    sleep(sleep_time)

    job.save()
    print('job done')
    # return datetime.now() - st


def import_csv_data_task(upload_job: UploadFileJob):
    upload_job.job_status = UploadFileJob.JobStatus.PROCESSING
    upload_job.save()
    try:
        file = upload_job.file
        if upload_job.labeling_job.job_data_type in {LabelingJob.DataTypes.SUPERVISE_MODEL,
                                                     LabelingJob.DataTypes.TERM_WEIGHT_MODEL}:
            create_documents(file, upload_job.labeling_job, update_labels=True, required_fields=DOCUMENT_FIELDS_MAPPING)
        elif upload_job.labeling_job.job_data_type in {LabelingJob.DataTypes.RULE_BASE_MODEL,
                                                       LabelingJob.DataTypes.REGEX_MODEL}:
            create_rules(file, upload_job.labeling_job, update_labels=True)
        else:
            raise ValueError(f'Unknown job_data_type {upload_job.labeling_job}.')
        upload_job.job_status = UploadFileJob.JobStatus.DONE
    except Exception as e:
        print(e)
        upload_job.job_status = UploadFileJob.JobStatus.ERROR
    finally:
        upload_job.save()


def read_csv_file(file, required_fields):
    delimiters = [',', '\t']
    encoding = cchardet.detect(file.read())['encoding']
    file.seek(0)
    csv_file = header = exist_field = None
    for delimiter in delimiters:
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                  delimiter=delimiter,
                                  quoting=csv.QUOTE_ALL)
        header = csv_file.fieldnames
        print(header)
        if isinstance(required_fields, dict):
            if len(set(required_fields.keys()).intersection(header)) > 0:
                exist_field = set(required_fields.keys()).intersection(header)
                break
            elif len(set(required_fields.values()).intersection(header)) > 0:
                exist_field = set(required_fields.values()).intersection(header)
                break
        else:
            if len(set(required_fields).intersection(header)) > 0:
                exist_field = set(required_fields).intersection(header)
                break
    if csv_file is None or exist_field is None:
        raise ValueError(f"csv欄位讀取錯誤，請確認所使用的欄位分隔符號是否屬於於「{' or '.join(delimiters)}」其中一種。")

    return csv_file


def create_rules(file, job: LabelingJob, required_fields=None, update_labels: bool = False):
    if job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
        required_fields = RULE_FIELDS_MAPPING if not required_fields else required_fields
        rule_type = Rule.RuleType.KEYWORD
    elif job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
        required_fields = REGEX_FIELDS_MAPPING if not required_fields else required_fields
        rule_type = Rule.RuleType.REGEX
    else:
        raise ValueError(f'Job {job} is not a rule base job.')
    csv_rows = read_csv_file(file, required_fields)
    rule_bulk_list = []
    job_labels_dict = job.get_labels_dict()

    exist_fields = set(Rule.__dict__.keys()).intersection(required_fields.keys())
    for index, row in enumerate(csv_rows):
        data = defaultdict(str)
        for _field in exist_fields:
            field_data = row.get(_field, None) or row.get(required_fields.get(_field), None)
            if _field == 'score':
                field_data = field_data if field_data else 1
            data[_field] = field_data
        label_str: str = data.get('label', None)
        match_types_str = data.get('match_type', None)
        content = data.get('content', None)
        score = data.get('score', 1)

        # 若沒有比對字詞或規則就不建立
        if content is None:
            continue

        # 取得Label物件
        if label_str in job_labels_dict:
            label_obj = job_labels_dict.get(label_str)
        elif update_labels:
            job.label_set.create(name=label_str, labeling_job=job)
            job.save()
            job_labels_dict = job.get_labels_dict()
            label_obj = job_labels_dict.get(label_str)
        else:
            continue

        if job.job_data_type == LabelingJob.DataTypes.RULE_BASE_MODEL:
            if match_types_str:
                if match_types_str.__contains__(','):
                    match_types = match_types_str.split(',')
                else:
                    match_types = [match_types_str]
            else:
                match_types = [Rule.MatchType.PARTIALLY]

            for match_type in match_types:
                if match_type not in Rule.MatchType:
                    match_type = Rule.MatchType.PARTIALLY

                rule = Rule(match_type=Rule.MatchType(match_type),
                            score=score,
                            content=content,
                            labeling_job=job,
                            rule_type=rule_type,
                            label=label_obj)
                print(rule.label, rule.match_type, rule.score, rule.content)
                rule_bulk_list.append(rule)
        elif job.job_data_type == LabelingJob.DataTypes.REGEX_MODEL:
            rule = Rule(score=score,
                        content=content,
                        rule_type=rule_type,
                        labeling_job=job,
                        label=label_obj)
            rule_bulk_list.append(rule)

    job.rule_set.bulk_create(rule_bulk_list, ignore_conflicts=True)


def create_documents(file, job: LabelingJob, required_fields=None, document_type: Document.TypeChoices = None,
                     update_labels: bool = False):
    if required_fields is None:
        required_fields = DOCUMENT_FIELDS_MAPPING
    csv_rows = read_csv_file(file, required_fields)
    print(csv_rows.fieldnames)

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    hash_str = dt_string + file.name

    doc_bulk_list = []
    m = hashlib.md5()
    m.update(hash_str.encode("utf-8"))
    hash_num = m.hexdigest()

    labels = []
    exist_fields = set(Document.__dict__.keys()).intersection(DOCUMENT_FIELDS_MAPPING.keys())
    print(exist_fields)
    for index, row in enumerate(csv_rows):
        data = defaultdict(str)
        for field in exist_fields:
            if field == 'post_time':
                _row = row.get(field, None) or row.get(DOCUMENT_FIELDS_MAPPING.get(field), None)
                _row = datetime.strptime(_row, "%Y/%m/%d %H:%M:%S") if _row else _row
            else:
                _row = row.get(field, None) or row.get(DOCUMENT_FIELDS_MAPPING.get(field), 'Unknown')
            data[field] = _row
        doc = Document(labeling_job_id=job.id,
                       hash_num=hash_num, **data)
        if document_type:
            doc.document_type = document_type
        doc_bulk_list.append(doc)
        labels.append(row.get("label", None) or row.get(DOCUMENT_FIELDS_MAPPING.get("label"), ''))

    job.document_set.bulk_create(doc_bulk_list)
    documents = job.document_set.filter(hash_num=hash_num)

    job_labels_dict = job.get_labels_dict()
    for index, doc in enumerate(documents):
        label = labels[index]

        if label is not None:
            for _label_name in label.split(','):
                _label_name = _label_name.strip()
                label_object = job_labels_dict.get(_label_name, None)
                # print(_label_name, label_object)
                if label_object:
                    doc.labels.add(label_object)
                elif update_labels:
                    doc.labels.create(name=_label_name, labeling_job_id=job.id)
                    doc.save()
                    job_labels_dict = job.get_labels_dict()
    return documents.count()


def set_type(docs: List[Document], doc_type=Document.TypeChoices.choices):
    for doc in docs:
        doc.document_type = doc_type
        doc.save()
    return docs


def generate_datasets_task(job: LabelingJob, train: float = 0.8, dev: float = 0.1, test: float = 0.1):
    """

    :param job:
    :param train: percentage of train set, 0~1
    :param dev: percentage of dev set, 0~1
    :param test: percentage of test set, 0~1
    :return:
    """
    labels: List[Label] = job.label_set.all()
    assert 0 < train < 1, "train should between 0 ~ 1"
    assert 0 < dev < 1, "train should between 0 ~ 1"
    assert 0 < test < 1, "train should between 0 ~ 1"
    assert (train + dev + test) <= 1, "sum of train, dev, test should less then 1"
    label_count = {}
    for label in labels:
        docs = job.document_set.all().filter(labels=label)
        doc_num = docs.count()
        train_count = round(train * doc_num)
        dev_count = round(dev * doc_num)
        test_count = round(test * doc_num)
        docs = list(docs)
        shuffle(list(docs))

        train_set = set_type(docs[:train_count], doc_type=Document.TypeChoices.TRAIN)
        dev_set = set_type(docs[train_count:train_count + dev_count],
                           doc_type=Document.TypeChoices.DEV)
        test_set = set_type(docs[-test_count:],
                            doc_type=Document.TypeChoices.TEST)
        label_count[label] = (len(train_set), len(dev_set), len(test_set))
    print(label_count)
