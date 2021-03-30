from django.db import models
from labeling_jobs.models import LabelingJob

class MLModel(models.Model):
    name = models.CharField(max_length=50,verbose_name="模型種類")
    def __str__(self):
        return self.name


class ModelingJob(models.Model):
    name = models.CharField(max_length=100,verbose_name="模型名稱")
    description = models.CharField(max_length=100,verbose_name="模型敘述")
    is_multi_label = models.BooleanField(verbose_name="是否為多標籤")
    model = models.ForeignKey(MLModel,on_delete=models.SET_NULL,blank=True,null=True)
    jobRef = models.ForeignKey(LabelingJob,on_delete=models.SET_NULL,blank=True,null=True)
    def __str__(self):
        return self.name