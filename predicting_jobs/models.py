from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse

from audience_toolkits.settings import PREDICT_DATABASE
from labeling_jobs.models import Label, Document
from modeling_jobs.models import ModelingJob


class JobStatus(models.TextChoices):
    WAIT = ('wait', '等待中')
    PROCESSING = ('processing', '處理中')
    BREAK = ('break', '中斷')
    ERROR = ('error', '錯誤')
    DONE = ('done', '完成')


class PredictingJob(models.Model):
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
    predicting_job = models.ForeignKey(PredictingJob, on_delete=models.CASCADE)
    modeling_job = models.ForeignKey(ModelingJob, verbose_name="應用模型任務", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.modeling_job.name if self.modeling_job else ""

    class Meta:
        unique_together = ('predicting_job', 'modeling_job',)
        verbose_name = "應用模型"
        verbose_name_plural = "應用模型列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.predicting_job_id})


class Source(models.Model):
    name = models.CharField(max_length=100, verbose_name="來源名稱")
    description = models.TextField(verbose_name="定義與說明")
    host = models.CharField(max_length=200, verbose_name="資料庫位置", null=True,
                            default=PREDICT_DATABASE.get("source", {}).get("HOST"))
    username = models.CharField(max_length=100, verbose_name="資料庫使用者", null=True,
                                default=PREDICT_DATABASE.get("source", {}).get("USER"))
    password = models.CharField(max_length=100, verbose_name="資料庫密碼", null=True,
                                default=PREDICT_DATABASE.get("source", {}).get("PASSWORD"))
    port = models.IntegerField(verbose_name="資料庫連接埠",
                               default=int(PREDICT_DATABASE.get("source", {}).get("PORT")))
    schema = models.CharField(max_length=100, verbose_name="資料庫名稱", null=True,
                              default=PREDICT_DATABASE.get("source", {}).get("SCHEMA"))
    tablename = models.CharField(max_length=100, verbose_name="資料表名稱",
                                 default=PREDICT_DATABASE.get("source", {}).get("TABLE"))
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
    job_status = models.CharField(max_length=20, verbose_name="任務狀態", default=JobStatus.WAIT, choices=JobStatus.choices)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "預測範圍"
        verbose_name_plural = "預測範圍列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.predicting_job_id})


class PredictingResult(models.Model):
    """
    預測結果，供預測結果抽樣驗證用，最終會輸出至rd4的db供rd5建索引。建索引需要的欄位為source_author（<s_id>_<author>）, panel（label_name）。
    注意：在匯出時不要清空rd5建索引的表格，可用update與insert，且必須於成功建完索引後將結果清掉，避免資料庫太肥大。
    """
    predicting_target = models.ForeignKey(PredictingTarget, verbose_name="預測資料範圍", on_delete=models.CASCADE)
    label_name = models.CharField(max_length=200, verbose_name="標籤名稱")
    score = models.FloatField(verbose_name="預測分數")
    data_id = models.CharField(max_length=200, verbose_name="預測文章ID")
    apply_path = models.JSONField(verbose_name="模型預測路徑", null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.data_id} result"

    class Meta:
        verbose_name = "預測結果"
        verbose_name_plural = "預測結果列表"

    def get_absolute_url(self):
        return reverse('predicting_jobs:job-detail', kwargs={'pk': self.predicting_target.predicting_job.id})
