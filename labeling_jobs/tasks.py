import codecs
import csv
import hashlib
from datetime import datetime
from time import sleep

import cchardet

from labeling_jobs.models import LabelingJob, Document, UploadFileJob


def sample_task(job: UploadFileJob, sleep_time=5):
    st = datetime.now()
    print(f'start doing job {job.file}')
    job.job_status = UploadFileJob.JobStatus.PROCESSING
    job.save()
    sleep(sleep_time)
    job.job_status = UploadFileJob.JobStatus.DONE
    job.save()
    print('job done')
    return datetime.now() - st


def import_csv_data_task(file, labeling_job_id):
    encoding = cchardet.detect(file.read())['encoding']
    file.seek(0)
    csv_file = csv.DictReader(codecs.iterdecode(file, encoding))
    title = csv_file.fieldnames
    required_fields = ['title', 'author', 's_area_id', 'content', 'label']
    result = True
    if set(title) != set(required_fields):
        return False

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    hash_str = dt_string + file.name

    doc_bulk_list = []
    m = hashlib.md5()
    m.update(hash_str.encode("utf-8"))
    hash_num = m.hexdigest()

    job: LabelingJob = LabelingJob.objects.get(pk=labeling_job_id)
    labels = []

    for index, row in enumerate(csv_file):
        doc = Document(title=row.get("title", ""),
                       author=row.get("author", ""),
                       s_area_id=row.get("s_area_id", ""),
                       content=row.get("content", ""),
                       post_time=row.get("post_time", None),
                       labeling_job_id=job.id,
                       hash_num=hash_num)
        doc_bulk_list.append(doc)
        labels.append(row.get("label", None))

    job.document_set.bulk_create(doc_bulk_list)

    documents = job.document_set.filter(hash_num=hash_num)
    for index, doc in enumerate(documents):
        label = labels[index]
        if label:
            if len(ls := job.label_set.filter(name=label)) > 0:
                l = ls.first()
                doc.labels.add(l)
            else:
                doc.labels.create(name=label, labeling_job_id=job.id)
    return result
