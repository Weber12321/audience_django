from django import forms
from django.contrib.auth.models import User

from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["name", "description", "created_by", "is_multi_label"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'is_multi_label': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'created_by': forms.TextInput(attrs={'hidden': True})
        }
        labels = {
            'name': '任務名稱',
            'description': '描述與定義'
        }
