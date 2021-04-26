import codecs
import csv
import hashlib
import json
from datetime import datetime

import cchardet

from labeling_jobs.models import LabelingJob, Document


def insert_csv_to_db(file, job_id):
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

    job: LabelingJob = LabelingJob.objects.get(pk=job_id)
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


def parse_report(report):
    report = report.replace("\'", "\"")
    report = json.loads(report)

    for key in report.keys():
        if key != 'accuracy':
            for i in report[key]:
                report[key][i] = round(report[key][i], 3)

    return report