from django.contrib import admin

# Register your models here.
from predicting_jobs.models import PredictingJob, Source, PredictingTarget


class PredictingTargetAdminInline(admin.TabularInline):
    model = PredictingTarget
    extra = 0


class PredictingJobAdmin(admin.ModelAdmin):
    model = PredictingJob
    fieldsets = [
        (
            None, {
                "fields": ['name', 'description', 'apply_models']
            }),
    ]
    inlines = [PredictingTargetAdminInline]
    list_display = (
        'name', 'updated_at', 'created_by')
    list_filter = ['created_at', "updated_at", 'created_by']
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


admin.site.register(PredictingJob, PredictingJobAdmin)
admin.site.register(PredictingTarget, PredictingTargetAdmin)
admin.site.register(Source, SourceAdmin)
