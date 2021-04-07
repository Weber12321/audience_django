from django.contrib import admin

# Register your models here.
from predicting_jobs.models import PredictingJob, Source, PredictingTarget, ApplyingModel


class PredictingTargetAdminInline(admin.TabularInline):
    model = PredictingTarget
    extra = 0


class ApplyingModelAdminInline(admin.TabularInline):
    model = ApplyingModel
    extra = 0


class PredictingJobAdmin(admin.ModelAdmin):
    model = PredictingJob
    fieldsets = [
        (
            None, {
                "fields": ['name', "job_status", 'description']
            }),
    ]
    inlines = [ApplyingModelAdminInline, PredictingTargetAdminInline]
    list_display = (
        'name', "job_status", 'updated_at', 'created_by')
    list_filter = ['created_at', "job_status", "updated_at", 'created_by']
    search_fields = ['name', 'description', 'created_by']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        if formset.model == PredictingJob:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.created_by = request.user
                instance.save()
        else:
            formset.save()


class SourceAdmin(admin.ModelAdmin):
    model = Source
    fieldsets = [
        (
            None, {
                "fields": ['name', 's_area_id', 'description']
            }),
    ]
    list_display = (
        'name', 'created_at', 'updated_at', 'created_by')
    list_filter = ['created_at', "updated_at", 'created_by']
    search_fields = ['name', 'description', 'created_by']

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

    def save_formset(self, request, form, formset, change):
        if formset.model == Source:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.created_by = request.user
                instance.save()
        else:
            formset.save()


class PredictingTargetAdmin(admin.ModelAdmin):
    model = PredictingTarget
    list_display = ('name', 'predicting_job', 'source', 'begin_post_time', 'end_post_time')
    search_fields = ['predicting_job', 'source', 'name', 'begin_post_time', 'end_post_time']
    list_filter = ['predicting_job', 'source', 'begin_post_time', 'end_post_time']


class ApplyingModelAdmin(admin.ModelAdmin):
    model = ApplyingModel
    list_display = ('modeling_job', 'predicting_job', 'priority')
    search_fields = ['predicting_job', 'modeling_job']
    list_filter = ['predicting_job', 'modeling_job']


admin.site.register(ApplyingModel, ApplyingModelAdmin)
admin.site.register(PredictingJob, PredictingJobAdmin)
admin.site.register(PredictingTarget, PredictingTargetAdmin)
admin.site.register(Source, SourceAdmin)
