from django.db import models
from labeling_jobs.models import LabelingJob


class MLModel(models.Model):
    name = models.CharField(max_length=50, verbose_name="模型種類")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "機器學習模型"
        verbose_name_plural = "機器學習模型列表"


class ModelingJob(models.Model):
    name = models.CharField(max_length=100, verbose_name="模型名稱")
    description = models.CharField(max_length=100, verbose_name="模型敘述")
    is_multi_label = models.BooleanField(verbose_name="是否為多標籤")
    model = models.ForeignKey(MLModel, on_delete=models.SET_NULL, blank=True, null=True)
    jobRef = models.ForeignKey(LabelingJob, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.BooleanField(verbose_name="是否已被訓練過", default=False, blank=True)

    def __str__(self):
        return self.name


class Report(models.Model):
    accuracy = models.FloatField(max_length=10, verbose_name='準確率', blank=True)
    report = models.CharField(max_length=1000, verbose_name='報告')
    models_ref = models.ForeignKey(ModelingJob, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.report
