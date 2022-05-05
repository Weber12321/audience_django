import uuid

from django.contrib.auth.models import User
from django.db import models

from django.urls import reverse


def hex_uuid():
    return uuid.uuid1().hex


class DocumentingJob(models.Model):
    name = models.CharField(max_length=100, verbose_name="標記任務名稱", default="Job")
    description = models.TextField(verbose_name="定義與說明")
    task_id = models.UUIDField(default=hex_uuid, unique=True, editable=False,
                               verbose_name="audience api 任務 ID")
    create_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "資料整備工作"
        verbose_name_plural = "資料整備工作列表"

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse('documenting_jobs:job-detail', kwargs={'pk': self.pk})



