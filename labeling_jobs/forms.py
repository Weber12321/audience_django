from django import forms

from .models import LabelingJob, Label, UploadFileJob, Rule


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


class RuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        labeling_job_id = kwargs.pop('labeling_job_id', None)
        super(RuleForm, self).__init__(*args, **kwargs)
        if labeling_job_id:
            self.fields['label'].queryset = Label.objects.filter(
                labeling_job_id=labeling_job_id)
        else:
            self.fields['label'].queryset = self.instance.labeling_job.label_set.all()

    class Meta:
        model = Rule
        fields = "__all__"
        exclude = ['labeling_job', 'created_at', 'created_by', 'rule_type']


class RegexForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        labeling_job_id = kwargs.pop('labeling_job_id', None)
        super(RegexForm, self).__init__(*args, **kwargs)
        if labeling_job_id:
            self.fields['label'].queryset = Label.objects.filter(
                labeling_job_id=labeling_job_id)
        else:
            self.fields['label'].queryset = self.instance.labeling_job.label_set.all()

    class Meta:
        model = Rule
        fields = "__all__"
        exclude = ['labeling_job', 'created_at', 'created_by', 'match_type', 'score', 'rule_type']


class DocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        if self.instance.labeling_job_id:
            self.fields['label'].queryset = Label.objects.filter(
                labeling_job_id=self.instance.labeling_job_id)
