import uuid

from django import forms

from .models import DocumentingJob


# class DocumentingJobForm(forms.ModelForm):
#     class Meta:
#         model = DocumentingJob
#         fields = '__all__'
#         exclude = ['create_by', 'is_multi_label']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control',
#                                            'value': f'Jab'}),
#             'description': forms.Textarea(attrs={'class': 'form-control'}),
#             'job_type': forms.Select(attrs={'class': 'form-control'}),
#         }

class DocumentingJobForm(forms.Form):
    document_task_type = (
        ('machine_learning_task', '機器學習模型資料'),
        ('rule_task', '規則模型資料')
    )
    name = forms.CharField(max_length=100, label='任務名稱')
    description = forms.CharField(
        label='任務簡述',
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '30'})
    )
    task_type = forms.ChoiceField(label='任務類型', choices=document_task_type)
    is_multi_label = forms.BooleanField(label='是否為多標籤', required=False)


class DatasetUpdateForm(forms.Form):
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


class RulesUpdateForm(forms.Form):
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





