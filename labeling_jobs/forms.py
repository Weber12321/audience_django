from django import forms

from .models import LabelingJob, Label, UploadFileJob


class UploadFileJobForm(forms.ModelForm):
    class Meta:
        model = UploadFileJob
        fields = '__all__'
        exclude = ['labeling_job', 'job_status', 'created_by']


class LabelingJobForm(forms.ModelForm):
    class Meta:
        model = LabelingJob
        fields = "__all__"
        exclude = ['created_by']
        # last_job_id = 0  # LabelingJob.objects.last().id if LabelingJob.objects.last() is not None else 0
        # widgets = {
        #     'name': forms.TextInput(attrs={'class': 'form-control',
        #                                    'value': f'Jab'}),
        #     'description': forms.Textarea(attrs={'class': 'form-control'}),
        #     'job_type': forms.Textarea(attrs={'class': 'form-control'}),
        #     'is_multi_label': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        #     'created_by': forms.TextInput(attrs={'hidden': True})
        # }
        # labels = {
        #     'name': '任務名稱',
        #     'job_type': '任務類型',
        #     'description': '描述與定義',
        #     "is_multi_label": '是否為多標籤分類'
        # }


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ["name", "description", "target_amount"]
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
                labeling_job_id=self.instance.labeling_job_id)
