from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse

from audience_toolkits import settings


class LabelingJob(models.Model):
    class DataTypes(models.TextChoices):
        SUPERVISE_MODEL = ("supervise_model", "監督式學習模型")
        RULE_BASE_MODEL = ("rule_base", "規則模型")
        REGEX_MODEL = ("regex", "正則表達式模型")
        TERM_WEIGHT_MODEL = ("term_weight", "詞彙權重模型")

    name = models.CharField(max_length=100, verbose_name="標記工作名稱", default="Job")
    description = models.TextField(verbose_name="定義與說明")
    is_multi_label = models.BooleanField(default=False, verbose_name="是否屬於多標籤")
    job_data_type = models.CharField(max_length=20, choices=DataTypes.choices, verbose_name="任務類型",
                                     default=DataTypes.SUPERVISE_MODEL)
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
        return self.document_set.count()

    show_document_amount.boolean = False
    show_document_amount.short_description = '文章數量'

    def get_train_set(self):
        return self.document_set.filter(document_type=Document.TypeChoices.TRAIN, labels__isnull=False)

    def get_dev_set(self):
        return self.document_set.filter(document_type=Document.TypeChoices.DEV, labels__isnull=False)

    def get_test_set(self):
        return self.document_set.filter(document_type=Document.TypeChoices.TEST, labels__isnull=False)

    def get_ext_test_set(self):
        return self.document_set.filter(document_type=Document.TypeChoices.EXT_TEST, labels__isnull=False)

    def get_labels_dict(self):
        return {label_object.name: label_object for label_object in self.label_set.all()}


class Label(models.Model):
    class TypeChoices(models.TextChoices):
        GROUND_TRUTH = ("ground_truth", "正確標記")
        PREDICTED = ("predicted", "預測標記")
        HUMAN = ("human", "人類標記")

    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="所屬任務")
    name = models.CharField(max_length=100, verbose_name="標籤名稱")
    description = models.TextField(verbose_name="標籤定義", blank=True)
    target_amount = models.IntegerField(verbose_name="目標數量", default=200)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更改")

    class Meta:
        verbose_name = "類別標籤"
        verbose_name_plural = "類別標籤列表"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('labeling_jobs:label-detail', kwargs={'job_id': self.labeling_job.id, 'pk': self.pk})

    def show_document_amount(self):
        return self.document_set.exclude(document_type=Document.TypeChoices.EXT_TEST).count()

    def show_progress_percentage(self):
        return round(self.show_document_amount() / self.target_amount * 100, 2)

    show_document_amount.boolean = False
    show_document_amount.short_description = '已標記文章數量'

    def show_train_set_count(self):
        return self.document_set.filter(document_type='train').count()

    def show_dev_set_count(self):
        return self.document_set.filter(document_type='dev').count()

    def show_test_set_count(self):
        return self.document_set.filter(document_type='test').count()

    def show_ext_test_set_count(self):
        return self.document_set.filter(document_type='ext_test').count()


class Document(models.Model):
    class TypeChoices(models.TextChoices):
        TRAIN = ("train", "訓練資料")
        DEV = ("dev", "驗證資料")
        TEST = ("test", "測試資料")
        EXT_TEST = ("ext_test", "額外測試資料")

    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="所屬任務")
    title = models.CharField(max_length=512, verbose_name="標題", blank=True)
    author = models.CharField(max_length=200, verbose_name="作者", blank=True)
    s_id = models.CharField(max_length=100, verbose_name="來源id", blank=True)
    s_area_id = models.CharField(max_length=100, verbose_name="頻道id", blank=True)
    content = models.TextField(verbose_name="內文", blank=True)
    post_time = models.DateTimeField(verbose_name="發布時間", blank=True, null=True)
    labels = models.ManyToManyField(Label, verbose_name="正確標籤", blank=True)
    hash_num = models.CharField(max_length=50, verbose_name='雜湊值', blank=True)
    document_type = models.CharField(max_length=10, choices=TypeChoices.choices, default=None, null=True)

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


class UploadFileJob(models.Model):
    class JobStatus(models.TextChoices):
        WAIT = ('wait', '等待中')
        PROCESSING = ('processing', '處理中')
        BREAK = ('break', '中斷')
        ERROR = ('error', '錯誤')
        DONE = ('done', '完成')

    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="所屬任務")
    file = models.FileField(upload_to=settings.UPLOAD_FILE_DIRECTORY, verbose_name="檔案")
    job_status = models.CharField(max_length=20, verbose_name="任務狀態", default=JobStatus.WAIT, choices=JobStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = "文件上傳任務"
        verbose_name_plural = "文件上傳任務列表"


class HumanLabeling(models.Model):
    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE, verbose_name="標記任務")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, verbose_name="文件")
    human_labels = models.ManyToManyField(Label, verbose_name="標記標籤")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"doc_id={self.document.id}, human={self.human_labels.all()}, ground_truth={self.document.labels.all()}"

    class Meta:
        verbose_name = "人員標記"
        verbose_name_plural = "人員標記列表"


class Rule(models.Model):
    class RuleType(models.TextChoices):
        KEYWORD = ('keyword', '關鍵字')
        REGEX = ('regex', '正則表達式')
        TERM_WEIGHT = ('term_weight', '詞彙加權')

    class MatchType(models.TextChoices):
        START = ('start', '比對開頭')
        END = ('end', '比對結尾')
        EXACTLY = ('exactly', '完全一至')
        PARTIALLY = ('partially', '部分吻合')

    labeling_job = models.ForeignKey(LabelingJob, on_delete=models.CASCADE)
    content = models.CharField(max_length=200, verbose_name="規則內文")
    label = models.ForeignKey(Label, verbose_name="標籤", on_delete=models.CASCADE)
    rule_type = models.CharField(max_length=20, verbose_name="規則類型", choices=RuleType.choices, default=RuleType.KEYWORD)
    match_type = models.CharField(max_length=20, verbose_name="比對方式", choices=MatchType.choices,
                                  default=MatchType.PARTIALLY)
    score = models.FloatField(verbose_name="命中分數", default=1)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"<'{self.label}'>, {self.score}, {self.content}"

    def get_absolute_url(self):
        return reverse('labeling_jobs:job-detail', kwargs={'pk': self.labeling_job.id})

    class Meta:
        verbose_name = "規則"
        verbose_name_plural = "規則列表"
        ordering = ('content', 'match_type',)
        unique_together = ('label', 'content', 'match_type',)
