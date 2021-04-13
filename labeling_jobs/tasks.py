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
    # your code here
    sleep(sleep_time)

    job.save()
    print('job done')
    # return datetime.now() - st


def import_csv_data_task(upload_job: UploadFileJob, required_fields=None):
    upload_job.job_status = UploadFileJob.JobStatus.PROCESSING
    upload_job.save()
    if required_fields is None:
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
                    l = ls.first()
                    doc.labels.add(l)
                else:
                    doc.labels.create(name=label, labeling_job_id=labeling_job.id)

        upload_job.job_status = UploadFileJob.JobStatus.DONE
    except Exception as e:
        print(e)
        upload_job.job_status = UploadFileJob.JobStatus.ERROR
    finally:
        upload_job.save()
