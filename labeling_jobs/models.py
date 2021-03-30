from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse


class LabelingJob(models.Model):
    name = models.CharField(max_length=100, verbose_name="標記工作名稱")
    description = models.TextField(verbose_name="定義與說明")
    is_multi_label = models.BooleanField(default=False, verbose_name="是否屬於多標籤")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "資料標記工作"
        verbose_name_plural = "資料標記工作列表"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('labeling_jobs:labeling-job-create', kwargs={'pk': self.pk})

    def show_labels(self):
        return [f"'{label.name}' ({label.target_amount})" for label in self.label_set.all()]

    show_labels.short_description = '存在標籤 (標記目標數量)'

    def show_target_amount(self):
        return sum([label.target_amount for label in self.label_set.all()])

    show_target_amount.short_description = '標記目標數量'

    def show_document_amount(self):
        return len(self.document_set.all())

    show_document_amount.boolean = False
    show_document_amount.short_description = '文章數量'


class Label(models.Model):
    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="所屬任務")
    name = models.CharField(max_length=100, verbose_name="標籤名稱")
    description = models.TextField(verbose_name="標籤定義")
    target_amount = models.IntegerField(verbose_name="目標數量", default=200)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")

    class Meta:
        verbose_name = "類別標籤"
        verbose_name_plural = "類別標籤列表"

    def __str__(self):
        return self.name

    def show_document_amount(self):
        return len(self.document_set.all())

    show_document_amount.boolean = False
    show_document_amount.short_description = '已標記文章數量'


class Document(models.Model):
    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="所屬任務")
    title = models.CharField(max_length=512, verbose_name="標題", blank=True)
    author = models.CharField(max_length=200, verbose_name="作者", blank=True)
    s_area_id = models.CharField(max_length=100, verbose_name="頻道id", blank=True)
    content = models.TextField(verbose_name="內文", blank=True)
    post_time = models.DateTimeField(verbose_name="發布時間", blank=True)
    labels = models.ManyToManyField(Label, verbose_name="被標記標籤", blank=True)

    class Meta:
        verbose_name = "文件"
        verbose_name_plural = "文件列表"

    def __str__(self):
        return self.title

    def show_labels(self):
        return [f'"{label.name}"' for label in self.labels.all()]

    show_labels.admin_order_field = 'updated_at'
    show_labels.boolean = False
    show_labels.short_description = '被標記標籤'
