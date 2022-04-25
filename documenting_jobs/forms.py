from django import forms

from .models import DocumentingJob


class DocumentingJobForm(forms.ModelForm):
    class Meta:
        model = DocumentingJob
        fields = '__all__'
        exclude = ['create_by', 'is_multi_label']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'value': f'Jab'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'is_multi_label': forms.CheckboxInput(attrs={'class': 'custom-switch'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'create_by': forms.TextInput(attrs={'hidden': True})
        }


class DatasetUpdateForm(forms.ModelForm):
    dataset_type_choices = (
        ('train', '訓練'),
        ('dev', '驗證'),
        ('test', '測試'),
        ('ext_text', '額外測試')
    )
    id = forms.IntegerField(label='文章編號')
    title = forms.CharField(max_length=512, label='文章標題')
    author = forms.CharField(max_length=100, label='文章作者')
    content = forms.CharField(label='文章內文', widget=forms.Textarea())
    dataset_type = forms.ChoiceField(label='資料集類型', choices=dataset_type_choices)
    task_id = forms.CharField(max_length=32)

    class Meta:
        exclude = ['task_id']


class RuleAddForm(forms.ModelForm):
    rule_type_choices = (
        ('keyword', '關鍵字規則'),
        ('regex', '正則式規則'),
        ('term_weight', '詞權重')
    )
    match_type_choices = (
        ('start', '比對開頭'),
        ('end', '比對結尾'),
        ('exactly', '完全一致'),
        ('partially', '部分吻合')
    )

    content = forms.CharField(max_length=200, label='規則內容')
    label = forms.CharField(max_length=100, label='標籤名稱')
    rule_type = forms.ChoiceField(label='規則類型', choices=rule_type_choices)
    match_type = forms.ChoiceField(label='比對方式', choices=match_type_choices)
    task_id = forms.CharField(max_length=32)

    class Meta:
        exclude = ['task_id']


class RulesUpdateForm(RuleAddForm):
    id = forms.IntegerField(label='文章編號')




