from django import forms

from .models import Job, Label, Document


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["name", "description", "is_multi_label"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'value': f'Jab {(Job.objects.last().id if Job.objects.last() is not None else 0) + 1}'}),
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


class DocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        if self.instance.job_id:
            self.fields['labels'].queryset = Label.objects.filter(
                job_id=self.instance.job_id)
