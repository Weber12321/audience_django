import codecs
import csv
import hashlib
from datetime import datetime
from random import shuffle
from time import sleep
from typing import List

import cchardet
from labeling_jobs.models import LabelingJob, Document, UploadFileJob, Label


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
        create_documents(file, upload_job.labeling_job, update_labels=True)
        upload_job.job_status = UploadFileJob.JobStatus.DONE
    except Exception as e:
        print(e)
        upload_job.job_status = UploadFileJob.JobStatus.ERROR
    finally:
        upload_job.save()


def create_documents(file, job: LabelingJob, required_fields=None, document_type: Document.TypeChoices = None,
                     update_labels: bool = False):
    if required_fields is None:
        required_fields = ['title', 'author', 's_area_id', 'content', 'label']

    delimiters = [',', '\t']
    encoding = cchardet.detect(file.read())['encoding']
    file.seek(0)
    csv_file = header = None
    for delimiter in delimiters:
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                  delimiter=delimiter,
                                  quoting=csv.QUOTE_ALL)
        header = csv_file.fieldnames
        if len(set(required_fields).intersection(header)) > 0:
            break
    if csv_file is None or header is None:
        raise ValueError(f"csv欄位讀取錯誤，請確認所使用的欄位分隔符號是否屬於於「{' or '.join(delimiters)}」其中一種。")

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    hash_str = dt_string + file.name

    doc_bulk_list = []
    m = hashlib.md5()
    m.update(hash_str.encode("utf-8"))
    hash_num = m.hexdigest()

    labels = []

    for index, row in enumerate(csv_file):
        doc = Document(title=row.get("title", ""),
                       author=row.get("author", ""),
                       s_area_id=row.get("s_area_id", ""),
                       content=row.get("content", ""),
                       post_time=row.get("post_time", None),
                       labeling_job_id=job.id,
                       hash_num=hash_num)
        if document_type:
            doc.document_type = document_type
        doc_bulk_list.append(doc)
        labels.append(row.get("label", None))

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
