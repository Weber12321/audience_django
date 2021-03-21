from django import forms
from django.contrib.auth.models import User

from .models import Job, Label


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["name", "description", "is_multi_label"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'value': f'Jab {Job.objects.last().id + 1}'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'is_multi_label': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'created_by': forms.TextInput(attrs={'hidden': True})
        }
        labels = {
            'name': '任務名稱',
            'description': '描述與定義',
            "is_multi_label": '是否為多標籤分類'
        }


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ["name", "description"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'created_by': forms.TextInput(attrs={'hidden': True})
        }
        labels = {
            'name': '標籤名稱',
            'description': '描述與定義'
        }
