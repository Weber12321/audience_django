from django.contrib import admin

from modeling_jobs.models import ModelingJob, MLModel


class ModelingJobAdmin(admin.ModelAdmin):
    model = ModelingJob


class MLModelAdmin(admin.ModelAdmin):
    model = MLModel


admin.site.register(MLModel, MLModelAdmin)
admin.site.register(ModelingJob, ModelingJobAdmin)
