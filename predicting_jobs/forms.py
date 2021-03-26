from django import forms

from .models import PredictingJob, Source


class PredictingJobForm(forms.ModelForm):
    class Meta:
        model = PredictingJob
        fields = ["name", "description"]
        last_job_id = PredictingJob.objects.last().id if PredictingJob.objects.last() is not None else 0
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
