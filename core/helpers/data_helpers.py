import cchardet
import csv
import codecs
from labeling_jobs.models import LabelingJob, Document, Label
from modeling_jobs.models import ModelingJob,Report
import hashlib
from datetime import datetime
import json

class DataHelper:
    def __init__(self):
        pass

    def insert_csv_to_db(self, file, job_id):
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

        for index,row in enumerate(csv_file):
            doc = Document(title=row.get("title", ""),
                           author=row.get("author", ""),
                           s_area_id=row.get("s_area_id", ""),
                           content=row.get("content", ""),
                           post_time=row.get("post_time", None),
                           labeling_job_id=job.id,
                           hash_num = hash_num)
            doc_bulk_list.append(doc)
            labels.append(row.get("label", None))

        job.document_set.bulk_create(doc_bulk_list)

        documents = job.document_set.filter(hash_num = hash_num)
        for index,doc in enumerate(documents):
            label = labels[index]
            if label:
                if len(ls := job.label_set.filter(name=label)) > 0:
                    l = ls.first()
                    doc.labels.add(l)
                else:
                    doc.labels.create(name=label, labeling_job_id=job.id)
        return result

    def get_training_data(self,labeling_job_id):
        documents = Document.objects.filter(labeling_job_id = labeling_job_id)
        content = []
        labels = []
        for doc in documents:
            content.append(doc.content)
            labels.append([label.name for label in doc.labels.all()])
        return content,labels

    def get_test_data(self,file):
        encoding = cchardet.detect(file.read())['encoding']
        file.seek(0)
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding))
        title = csv_file.fieldnames
        content = []
        labels = []
        required_fields = ['title', 'author', 's_area_id', 'content', 'label']
        if set(title) != set(required_fields):
            return content,labels
        else:
            for item in csv_file:
                content.append(item.get('content',''))
                labels.append(item.get('label',''))
            return content,labels

    def save_report(self,modeling_job_id,report):
        data = Report.objects.filter(models_ref_id = modeling_job_id)
        accuracy = report.get('accuracy', -1)
        if len(data) == 0:
            r = Report(accuracy = accuracy , report = str(report), models_ref_id = modeling_job_id)
            r.save()
        else:
            data.update(accuracy = accuracy,report = report)

    def get_report(self,modeling_job_id):
        modeling_job_id = int(modeling_job_id)
        print(modeling_job_id)
        report = Report.objects.get(models_ref_id = modeling_job_id)
        report = report.report
        report = report.replace("\'", "\"")
        report = json.loads(report)

        for key in report.keys():
            if key != 'accuracy':
                for i in report[key]:
                    report[key][i] = round(report[key][i],3)

        return report


    def get_labels(self,modeling_job_id):
        job = ModelingJob.objects.get(id = modeling_job_id)
        labeling_job_id = job.jobRef_id
        label_set = Label.objects.filter(labeling_job_id = labeling_job_id)
        labels = []
        for label in label_set:
            labels.append(label.name)
        return labels

