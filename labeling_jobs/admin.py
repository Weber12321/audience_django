from django.contrib import admin

# Register your models here.
from labeling_jobs.forms import DocumentForm
from labeling_jobs.models import LabelingJob, Label, Document, UploadFileJob, SampleData


class LabelInline(admin.TabularInline):
    model = Label
    extra = 0
    fields = ['name', 'description', 'target_amount']


class DocumentInline(admin.StackedInline):
    model = Document
    extra = 0
    fields = ['title', 's_area_id', 'author', 'content', 'post_time']


class UploadFileJobInline(admin.StackedInline):
    model = UploadFileJob
    extra = 0
    fields = ['file']


class SampleDataAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'created_at']
    list_display = ['name', 'job_data_type', 'created_by', 'created_at', 'file']
    search_fields = ['name', 'file']
    list_filter = ['job_data_type', 'created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()


class LabelingJobAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None, {
                "fields": ['name', 'description', 'is_multi_label']
            }),
    ]
    inlines = [LabelInline, UploadFileJobInline]
    list_display = (
        'name', 'is_multi_label', 'show_target_amount', 'show_document_amount', 'show_labels', 'created_at',
        'updated_at', 'created_by')
    list_filter = ['created_at', "updated_at", 'created_by']
    search_fields = ['name', 'description', 'created_by']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        if formset.model == LabelingJob:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.created_by = request.user
                instance.save()
        else:
            formset.save()


class DocumentAdmin(admin.ModelAdmin):
    model = Document
    list_display = ['title', 's_area_id', 'author', 'post_time', 'labeling_job']
    search_fields = ['title', 's_area_id', 'labeling_jobs']
    list_filter = ['post_time', 'labeling_job']
    form = DocumentForm


class LabelAdmin(admin.ModelAdmin):
    model = Label
    list_display = ('name', 'labeling_job', 'show_document_amount', 'target_amount', 'created_at', 'updated_at')
    list_filter = ['created_at', "updated_at", 'labeling_job']
    search_fields = ['name', 'description', 'labeling_job']


admin.site.register(LabelingJob, LabelingJobAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(SampleData, SampleDataAdmin)
