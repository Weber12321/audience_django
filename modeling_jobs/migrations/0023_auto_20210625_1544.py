# Generated by Django 3.1.8 on 2021-06-25 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modeling_jobs', '0022_merge_20210615_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelingjob',
            name='model_name',
            field=models.CharField(choices=[('SVM_MODEL', 'SVM'), ('RANDOM_FOREST', '隨機森林'), ('KEYWORD_MODEL', '關鍵字規則'), ('REGEX_MODEL', '正則表達式比對'), ('TERM_WEIGHT_MODEL', '詞彙權重模型')], max_length=50, verbose_name='模型類型'),
        ),
    ]