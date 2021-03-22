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
                "fields": ['name', 'description', 'is_multi_label']
            }),
    ]
    inlines = [LabelInline, DocumentInline]
    list_display = (
        'name', 'show_labels', 'is_multi_label', 'show_document_count', 'created_at', 'updated_at', 'created_by')
    list_filter = ['created_at', "updated_at", 'created_by']
    search_fields = ['name', 'description', 'created_by']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        if formset.model == Job:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.created_by = request.user
                instance.save()
        else:
            formset.save()


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
