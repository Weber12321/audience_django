import uuid

from django.contrib.auth.models import User
from django.db import models

from django.urls import reverse


class DocumentingJob(models.Model):
    class TaskType(models.TextChoices):
        MACHINE_LEARNING = ("machine_learning_task", "監督式學習模型")
        RULE = ("rule_task", "關鍵字與規則模型")

    name = models.CharField(max_length=100, verbose_name="標記任務名稱", default="Job")
    description = models.TextField(verbose_name="定義與說明")
    is_multi_label = models.BooleanField(default=False, verbose_name="是否屬於多標籤")
    job_type = models.CharField(max_length=100, choices=TaskType.choices,
                                verbose_name="任務類型", default=TaskType.RULE)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    update_time = models.DateTimeField(auto_now=True, verbose_name="最後修改時間")
    task_id = models.UUIDField(default=uuid.uuid1, unique=True, editable=False,
                               verbose_name="audience api 任務 ID")
    create_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "資料整備工作"
        verbose_name_plural = "資料整備工作列表"

    def __str__(self):
        return f"{self.name} ({self.get_job_type_display()})"

    def get_absolute_url(self):
        return reverse('documenting_jobs:job-detail', kwargs={'pk': self.pk})
