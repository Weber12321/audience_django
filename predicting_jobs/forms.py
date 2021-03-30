from django import forms
from django.forms import inlineformset_factory, modelformset_factory

from .models import PredictingJob, Source, PredictingTarget


class PredictingJobForm(forms.ModelForm):
    class Meta:
        model = PredictingJob
        fields = "__all__"
        # fields = ["name", "description"]
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
        fields = ['name', 'description', 'begin_post_time', 'end_post_time']
        widgets = {
            "begin_post_time":  forms.DateTimeInput(attrs={'type': 'datetime'}),
            "end_post_time": forms.DateTimeInput(attrs={'type': 'datetime'})
        }


TargetFormSet = modelformset_factory(model=PredictingTarget, form=PredictingTargetForm,
                                     extra=1)
