from django import forms

from .models import PredictingJob, PredictingTarget, ApplyingModel


class PredictingJobForm(forms.ModelForm):
    class Meta:
        model = PredictingJob
        fields = "__all__"
        exclude = ["created_by", "job_status"]
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


class PredictingTargetForm(forms.ModelForm):
    class Meta:
        model = PredictingTarget
        fields = '__all__'
        exclude = ['error_message', 'job_status']
        widgets = {
            "predicting_job": forms.Select(attrs={'class': 'form-control'}),
            "name": forms.TextInput(attrs={'class': 'form-control'}),
            "description": forms.Textarea(attrs={'class': 'form-control'}),
            "source": forms.Select(attrs={'class': 'form-control'}),
            "min_content_length": forms.NumberInput(attrs={'class': 'form-control'}),
            "max_content_length": forms.NumberInput(attrs={'class': 'form-control'}),
            "begin_post_time": forms.SelectDateWidget(attrs={
                'class': 'form-control',
            }),
            "end_post_time": forms.SelectDateWidget(attrs={
                'class': 'form-control',
            }),
        }


class ApplyingModelForm(forms.ModelForm):
    class Meta:
        model = ApplyingModel
        fields = '__all__'
        exclude = []
        widgets = {
            "predicting_job": forms.Select(attrs={'class': 'form-control'}),
            "modeling_job": forms.Select(attrs={'class': 'form-control'}),
            "priority": forms.NumberInput(attrs={'class': 'form-control'}),
        }
