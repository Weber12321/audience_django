from django.contrib import admin

from modeling_jobs.models import ModelingJob


class ModelingJobAdmin(admin.ModelAdmin):
    model = ModelingJob


admin.site.register(ModelingJob, ModelingJobAdmin)
