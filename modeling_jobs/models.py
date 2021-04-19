import json
from collections import namedtuple
from typing import Union, List, NamedTuple

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from audience_toolkits import settings
from labeling_jobs.models import LabelingJob, Document


class ModelingJob(models.Model):
    model_choices = [(key, value.get("verbose_name", key)) for key, value in settings.ML_MODELS.items()]

    class JobStatus(models.TextChoices):
        WAIT = ('wait', '等待中')
        PROCESSING = ('processing', '處理中')
        BREAK = ('break', '中斷')
        ERROR = ('error', '錯誤')
        DONE = ('done', '完成')

    name = models.CharField(max_length=100, verbose_name="模型名稱")
    description = models.CharField(max_length=100, verbose_name="模型敘述")
    is_multi_label = models.BooleanField(verbose_name="是否為多標籤")
    model_type = models.CharField(max_length=50, choices=model_choices)
    jobRef = models.ForeignKey(LabelingJob, verbose_name="使用資料", on_delete=models.SET_NULL, blank=True, null=True)
    job_train_status = models.CharField(max_length=20, verbose_name="模型訓練狀態", default=JobStatus.WAIT,
                                        choices=JobStatus.choices, blank=True, null=True)
    job_test_status = models.CharField(max_length=20, verbose_name="模型測試狀態", default=JobStatus.WAIT,
                                       choices=JobStatus.choices, blank=True, null=True)
    model_path = models.CharField(max_length=100, verbose_name="模型存放位置", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "模型訓練任務"
        verbose_name_plural = "模型訓練任務列表"

    def get_absolute_url(self):
        return reverse('modeling_jobs:job-detail', kwargs={'pk': self.id})

    def get_latest_train_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.TRAIN).last()
        if report:
            report.report = json.loads(report.report)
            report.report.pop('accuracy')
        return report

    def get_latest_dev_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.DEV).last()
        if report:
            report.report = json.loads(report.report)
            report.report.pop('accuracy')
        return report

    def get_latest_test_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.TEST).last()
        if report:
            report.report = json.loads(report.report)
            report.report.pop('accuracy')
        return report


class Report(models.Model):
    dataset_type = models.CharField(max_length=10, choices=Document.TypeChoices.choices, default=None, null=True)
    accuracy = models.FloatField(max_length=10, verbose_name='準確率', blank=True)
    report = models.CharField(max_length=1000, verbose_name='報告')
    modeling_job = models.ForeignKey(ModelingJob, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.report
