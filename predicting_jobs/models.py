from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse

from modeling_jobs.models import ModelingJob


class Source(models.Model):
    name = models.CharField(max_length=100, verbose_name="來源名稱")
    s_area_id = models.CharField(max_length=100, verbose_name="opv_id")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "資料源"
        verbose_name_plural = "資料源列表"


class PredictingJob(models.Model):
    name = models.CharField(max_length=100, verbose_name="預測工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    apply_sources = models.ManyToManyField(Source, blank=True, verbose_name="預測資料源列表")
    apply_models = models.ManyToManyField(ModelingJob, blank=True, verbose_name="使用模型列表")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "預測任務"
        verbose_name_plural = "預測任務列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.pk})
