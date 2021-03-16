from django.contrib import admin

# Register your models here.
from labeling_jobs.models import Job, Label, Document


class LabelInline(admin.TabularInline):
    model = Label
    extra = 0
    fields = ['name', 'description']


class DocumentInline(admin.StackedInline):
    model = Document
    extra = 0
    fields = ['title', 's_area_id', 'author', 'content', 'post_time']


class JobAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None, {
                "fields": ['name', 'description']
            }),
    ]
    inlines = [LabelInline, DocumentInline]
    list_display = ('name', 'show_labels', 'show_document_count', 'created_at', 'updated_at')
    list_filter = ['created_at', "updated_at"]
    search_fields = ['name', 'description']


class DocumentAdmin(admin.ModelAdmin):
    model = Document
    list_display = ['title', 's_area_id', 'author', 'post_time', 'job', 'show_labels']
    search_fields = ['title', 's_area_id']
    list_filter = ['post_time']


class LabelAdmin(admin.ModelAdmin):
    model = Label
    list_display = ('name', 'job', 'show_document_count', 'created_at', 'updated_at')
    list_filter = ['created_at', "updated_at"]
    search_fields = ['name', 'description']


admin.site.register(Job, JobAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Label, LabelAdmin)
