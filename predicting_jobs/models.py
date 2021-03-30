from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse

from modeling_jobs.models import ModelingJob


class PredictingJob(models.Model):

    class JobStatus(models.TextChoices):
        WAIT = ('wait', '等待中')
        PROCESSING = ('processing', '處理中')
        BREAK = ('break', '中斷')
        ERROR = ('error', '錯誤')
        DONE = ('done', '完成')

    name = models.CharField(max_length=100, verbose_name="預測工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="建立者", null=True)
    job_status = models.CharField(max_length=20, verbose_name="任務狀態", default=JobStatus.WAIT, choices=JobStatus.choices)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "預測任務"
        verbose_name_plural = "預測任務列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.pk})


class ApplyingModel(models.Model):
    predicting_job = models.ForeignKey(PredictingJob, on_delete=models.CASCADE, blank=True, null=True)
    modeling_job = models.ForeignKey(ModelingJob, verbose_name="應用模型任務", on_delete=models.CASCADE, blank=True,
                                     null=True)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.modeling_job.name

    class Meta:
        unique_together = ('predicting_job', 'modeling_job',)
        verbose_name = "應用模型"
        verbose_name_plural = "應用模型列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.predicting_job_id})


class Source(models.Model):
    name = models.CharField(max_length=100, verbose_name="來源名稱")
    s_area_id = models.CharField(max_length=100, verbose_name="opv_id")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="建立者", null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "資料源"
        verbose_name_plural = "資料源列表"


class PredictingTarget(models.Model):
    predicting_job = models.ForeignKey(PredictingJob, blank=True, verbose_name="預測任務", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="預測目標名稱")
    description = models.TextField(verbose_name="定義與說明")
    source = models.ForeignKey(Source, verbose_name="預測資料源", on_delete=models.SET_NULL, null=True, blank=True)
    begin_post_time = models.DateTimeField(verbose_name="起始發文時間")
    end_post_time = models.DateTimeField(verbose_name="結束發文時間")
    min_content_length = models.IntegerField(verbose_name='最小文章長度', default=10)
    max_content_length = models.IntegerField(verbose_name='最大文章長度', default=2000)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "預測範圍"
        verbose_name_plural = "預測範圍列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.predicting_job_id})
