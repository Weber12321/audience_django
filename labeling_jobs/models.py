from django.db import models


# Create your models here.

class Job(models.Model):
    name = models.CharField(max_length=200, verbose_name="標記工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    create_date = models.DateTimeField(verbose_name="建立時間")

    def __str__(self):
        return self.name


class Document(models.Model):
    labeling_job = models.ForeignKey(Job, on_delete=models.CASCADE)
    title = models.CharField(max_length=512, verbose_name="標題")
    author = models.CharField(max_length=200, verbose_name="作者")
    s_area_id = models.CharField(max_length=100, verbose_name="頻道id")
    content = models.TextField(verbose_name="內文")
    post_time = models.DateTimeField(verbose_name="發布時間")

    def __str__(self):
        return self.title


class Label(models.Model):
    labeling_job = models.ForeignKey(Job, on_delete=models.CASCADE)
    documents = models.ManyToManyField(Document)
    name = models.CharField(max_length=100, verbose_name="標籤名稱")
    description = models.TextField(verbose_name="標籤定義")

    def __str__(self):
        return self.name
