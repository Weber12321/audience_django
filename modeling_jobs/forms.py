from django import forms

from modeling_jobs.models import ModelingJob


class ModelingJobForm(forms.ModelForm):
    class Meta:
        model = ModelingJob
        fields = "__all__"
        exclude = ["model_path", "job_train_status", "job_test_status"]
        last_job_id = ModelingJob.objects.last().id if ModelingJob.objects.last() is not None else 0
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'value': f'Jab {last_job_id + 1}'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'created_by': forms.TextInput(attrs={'hidden': True})
        }
        labels = {
            'name': '任務名稱',
            'description': '描述與定義',
        }
