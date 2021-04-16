import codecs
import csv

from labeling_jobs.models import LabelingJob, Document, Label
import hashlib
import json
from datetime import datetime
import cchardet

from modeling_jobs.models import ModelingJob, Report


def get_test_data(file):
    delimiters = [',', '\t']
    encoding = cchardet.detect(file.read())['encoding']
    file.seek(0)
    csv_file = header = None
    for delimiter in delimiters:
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                  delimiter=delimiter,
                                  quoting=csv.QUOTE_ALL)
        header = csv_file.fieldnames
        if "content" in header and "label" in header:
            break

    print(header)
    content = []
    labels = []
    # required_fields = ['title', 'author', 's_area_id', 'content', 'label']
    required_fields = ['content', 'label']
    if set(header) != set(required_fields):
        return content, labels
    else:
        for item in csv_file:
            content.append(item.get('content', ''))
            labels.append(item.get('label', ''))
        return content, labels


def save_report(modeling_job_id, report):
    data = Report.objects.filter(models_ref_id=modeling_job_id)
    accuracy = report.get('accuracy', -1)
    if len(data) == 0:
        r = Report(accuracy=accuracy, report=str(report), models_ref_id=modeling_job_id)
        r.save()
    else:
        data.update(accuracy=accuracy, report=report)


def get_report(modeling_job_id):
    modeling_job_id = int(modeling_job_id)
    report = Report.objects.get(models_ref_id=modeling_job_id)
    report = report.report
    report = report.replace("\'", "\"")
    report = json.loads(report)

    for key in report.keys():
        if key != 'accuracy':
            for i in report[key]:
                report[key][i] = round(report[key][i], 3)

    return report


def get_labels(modeling_job_id):
    job = ModelingJob.objects.get(id=modeling_job_id)
    labeling_job_id = job.jobRef_id
    label_set = Label.objects.filter(labeling_job_id=labeling_job_id)
    labels = []
    for label in label_set:
        labels.append(label.name)
    return labels
