from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Job(models.Model):
    name = models.CharField(max_length=200, verbose_name="標記工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    updated_by = models.ForeignKey(User, related_name='job_updated_by', on_delete=models.DO_NOTHING, null=True)
    created_by = models.ForeignKey(User, related_name='job_created_by', on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.name

    def show_labels(self):
        return [f'"{label.name}"' for label in self.label_set.all()]

    show_labels.admin_order_field = 'updated_at'
    show_labels.boolean = False
    show_labels.short_description = '存在的標籤'

    def show_document_count(self):
        return len(self.document_set.all())

    show_document_count.boolean = False
    show_document_count.short_description = '文章數量'


class Label(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="所屬任務")
    # documents = models.ManyToManyField(Document)
    name = models.CharField(max_length=100, verbose_name="標籤名稱")
    description = models.TextField(verbose_name="標籤定義")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    updated_by = models.ForeignKey(User, related_name='label_updated_by', on_delete=models.DO_NOTHING, null=True)
    created_by = models.ForeignKey(User, related_name='label_created_by', on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.name

    def show_document_count(self):
        return len(self.document_set.all())

    show_document_count.boolean = False
    show_document_count.short_description = '文章數量'


class Document(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="所屬任務")
    title = models.CharField(max_length=512, verbose_name="標題")
    author = models.CharField(max_length=200, verbose_name="作者")
    s_area_id = models.CharField(max_length=100, verbose_name="頻道id")
    content = models.TextField(verbose_name="內文")
    post_time = models.DateTimeField(verbose_name="發布時間")
    labels = models.ManyToManyField(Label, verbose_name="被標記標籤")
    updated_by = models.ForeignKey(User, related_name='document_updated_by', on_delete=models.DO_NOTHING, null=True)
    created_by = models.ForeignKey(User, related_name='document_created_by', on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.title

    def show_labels(self):
        return [f'"{label.name}"' for label in self.labels.all()]

    show_labels.admin_order_field = 'updated_at'
    show_labels.boolean = False
    show_labels.short_description = '被標記標籤'
