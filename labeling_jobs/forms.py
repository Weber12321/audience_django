from django import forms

from .models import LabelingJob, Label


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()


class LabelingJobForm(forms.ModelForm):
    class Meta:
        model = LabelingJob
        fields = ["name", "description", "is_multi_label"]
        last_job_id = LabelingJob.objects.last().id if LabelingJob.objects.last() is not None else 0
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'value': f'Jab {last_job_id + 1}'}),
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
        if self.instance.labeling_job_id:
            self.fields['labels'].queryset = Label.objects.filter(
                job_id=self.instance.job_id)
