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


def import_csv_data_task(upload_job: UploadFileJob, required_fields=None):
    upload_job.job_status = UploadFileJob.JobStatus.PROCESSING
    upload_job.save()
    if required_fields is None:
        # todo 自動取得Document可用欄位，或者可於settings做設定
        # 可用[field.name for field in Document._meta.fields] 但需決定哪些事可用的
        required_fields = ['title', 'author', 's_area_id', 'content', 'label']
    try:
        file = upload_job.file
        encoding = cchardet.detect(file.read())['encoding']
        file.seek(0)
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                  delimiter=upload_job.delimiter,
                                  quoting=csv.QUOTE_ALL)
        title = csv_file.fieldnames
        if diff := set(title).difference(required_fields):
            print(title)
            print(required_fields)
            print(f"difference={diff}")

        now = datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        hash_str = dt_string + file.name

        doc_bulk_list = []
        m = hashlib.md5()
        m.update(hash_str.encode("utf-8"))
        hash_num = m.hexdigest()

        labeling_job: LabelingJob = LabelingJob.objects.get(pk=upload_job.labeling_job.id)
        labels = []

        for index, row in enumerate(csv_file):
            doc = Document(title=row.get("title", ""),
                           author=row.get("author", ""),
                           s_area_id=row.get("s_area_id", ""),
                           content=row.get("content", ""),
                           post_time=row.get("post_time", None),
                           labeling_job_id=labeling_job.id,
                           hash_num=hash_num)
            doc_bulk_list.append(doc)
            labels.append(row.get("label", None))

        labeling_job.document_set.bulk_create(doc_bulk_list)
        documents = labeling_job.document_set.filter(hash_num=hash_num)
        for index, doc in enumerate(documents):
            label = labels[index]
            if label:
                label = ",".join(set(label.split(',')))
                if len(ls := labeling_job.label_set.filter(name=label)) > 0:
                    _label = ls.first()
                    doc.labels.add(_label)
                else:
                    doc.labels.create(name=label, labeling_job_id=labeling_job.id)

        upload_job.job_status = UploadFileJob.JobStatus.DONE
    except Exception as e:
        print(e)
        upload_job.job_status = UploadFileJob.JobStatus.ERROR
    finally:
        upload_job.save()


def set_type(docs: List[Document], doc_type=Document.TypeChoices.choices):
    for doc in docs:
        doc.type = doc_type
        doc.save()
    return docs


def generate_datasets(job: LabelingJob, train: float = 0.8, dev: float = 0.1, test: float = 0.1):
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
