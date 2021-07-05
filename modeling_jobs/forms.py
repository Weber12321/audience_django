import logging

from django import forms

from labeling_jobs.models import Label
from modeling_jobs.models import ModelingJob, TermWeight, UploadModelJob

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ModelingJobForm(forms.ModelForm):
    class Meta:
        model = ModelingJob
        fields = "__all__"
        exclude = ["model_path", "job_status", "is_multi_label", "ext_test_status", "created_at", "created_by",
                   "error_message"]
        # last_job_id = ModelingJob.objects.last().id if ModelingJob.objects.last() is not None else 0
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'value': f'Jab'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '請描述模型的用途'}),
            'model_name': forms.Select(attrs={'class': 'form-control'}),
            'feature': forms.Select(attrs={'class': 'form-control'}),
            'jobRef': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': '任務名稱',
            'description': '描述與定義',
        }


class TermWeightForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        logger.debug(kwargs)
        modeling_job_id = kwargs.pop('modeling_job', None)
        super(TermWeightForm, self).__init__(*args, **kwargs)

        if hasattr(self.instance, 'modeling_job'):
            self.fields['label'].queryset = self.instance.modeling_job.jobRef.label_set.all()
        else:
            logger.debug(modeling_job_id)
            modeling_job = ModelingJob.objects.get(pk=modeling_job_id)
            self.fields['label'].queryset = modeling_job.jobRef.label_set.all()

    class Meta:
        model = TermWeight
        fields = "__all__"
        exclude = ['modeling_job', 'created_at', 'created_by', 'rule_type']


class UploadModelJobForm(forms.ModelForm):
    class Meta:
        model = UploadModelJob
        fields = '__all__'
        exclude = ['modeling_job', 'job_status', 'created_by']
        widgets = {
            'file': forms.FileInput(attrs={'class': '.form-control-file.', }),
        }
