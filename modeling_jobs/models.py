import json
from collections import namedtuple
from typing import Union, List, NamedTuple

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F
from django.urls import reverse

from audience_toolkits import settings
from core.helpers.model_helpers import get_model_class
from labeling_jobs.models import LabelingJob, Document, Label


class ModelingJob(models.Model):
    __model_choices__ = [(key, value.get("verbose_name", key)) for key, value in settings.ML_MODELS.items()]
    __feature_choices__ = [(key, value) for key, value in settings.AVAILABLE_FIELDS.items()]

    class JobStatus(models.TextChoices):
        WAIT = ('wait', '等待中')
        PROCESSING = ('processing', '處理中')
        BREAK = ('break', '中斷')
        ERROR = ('error', '錯誤')
        DONE = ('done', '完成')

    name = models.CharField(max_length=100, verbose_name="模型名稱")
    description = models.CharField(max_length=100, verbose_name="模型敘述")
    is_multi_label = models.BooleanField(default=False, verbose_name="是否為多標籤")
    model_name = models.CharField(max_length=50, choices=__model_choices__, verbose_name="模型類型")
    feature = models.CharField(max_length=50, choices=__feature_choices__, default='content', verbose_name="特徵欄位")
    jobRef = models.ForeignKey(LabelingJob, verbose_name="使用資料", on_delete=models.SET_NULL, blank=True, null=True)
    job_status = models.CharField(max_length=20, verbose_name="模型訓練狀態", default=JobStatus.WAIT,
                                  choices=JobStatus.choices)
    error_message = models.TextField(verbose_name="錯誤訊息", null=True)
    ext_test_status = models.CharField(max_length=20, verbose_name="模型測試狀態", default=JobStatus.WAIT,
                                       choices=JobStatus.choices)
    model_path = models.CharField(max_length=100, verbose_name="模型存放位置", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="建立者")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "模型訓練任務"
        verbose_name_plural = "模型訓練任務列表"

    def get_model_type(self):
        model_cls = get_model_class(self.model_name)
        if model_cls:
            return model_cls.__base__.__name__
        else:
            return None

    def is_trainable(self):
        model_cls = get_model_class(self.model_name)
        return hasattr(model_cls, "fit")

    def get_absolute_url(self):
        return reverse('modeling_jobs:job-detail', kwargs={'pk': self.id})

    def get_latest_train_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.TRAIN).last()
        return report

    def get_latest_dev_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.DEV).last()
        return report

    def get_latest_test_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.TEST).last()
        return report

    def get_latest_ext_test_report(self):
        report = self.report_set.filter(dataset_type=Document.TypeChoices.EXT_TEST).last()
        return report


class Report(models.Model):
    dataset_type = models.CharField(max_length=10, choices=Document.TypeChoices.choices, default=None, null=True)
    accuracy = models.FloatField(max_length=10, verbose_name='準確率', blank=True)
    report = models.CharField(max_length=1000, verbose_name='報告')
    modeling_job = models.ForeignKey(ModelingJob, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.dataset_type}, acc={self.accuracy}, created at {self.created_at}"

    class Meta:
        verbose_name = "驗證報告"
        verbose_name_plural = "驗證報告列表"

    def get_report(self):
        if self.report:
            report = json.loads(self.report)
            report.pop('accuracy')
            return report
        return None


class EvalPrediction(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, verbose_name="驗證報告")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, verbose_name="預測文件")
    prediction_labels = models.ManyToManyField(Label, verbose_name="預測標籤")

    def get_prediction(self):
        return self.prediction_labels.all()

    def get_ground_truth(self):
        return self.document.labels.all()

    def is_right_answer(self):
        prediction = set([label.name for label in self.get_prediction()])
        ground_truth = set([label.name for label in self.get_ground_truth()])
        return prediction == ground_truth

    def __str__(self):
        return f"doc_id={self.document.id}, " \
               f"prediction={self.prediction_labels.all()}, " \
               f"ground_truth={self.document.labels.all()}"

    class Meta:
        verbose_name = "驗證標記"
        verbose_name_plural = "驗證標記列表"


class TermWeight(models.Model):
    modeling_job = models.ForeignKey(ModelingJob, on_delete=models.CASCADE, verbose_name="模型訓練任務")
    term = models.CharField(max_length=20, verbose_name="詞彙")
    weight = models.FloatField(verbose_name="權重分數")
    label = models.ForeignKey(Label, on_delete=models.CASCADE, verbose_name="所屬標籤")

    class Meta:
        verbose_name = "詞彙權重"
        verbose_name_plural = "詞彙權重列表"
        ordering = ('modeling_job', 'label', F('weight').desc(nulls_last=True), 'term')
        unique_together = ("modeling_job", "term", "label")
