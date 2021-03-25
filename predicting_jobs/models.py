from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class PredictingTask(models.Model):
    name = models.CharField(max_length=100, verbose_name="預測工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)

