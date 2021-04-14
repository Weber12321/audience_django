# Generated by Django 3.1.7 on 2021-04-14 09:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('labeling_jobs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='模型種類')),
            ],
            options={
                'verbose_name': '機器學習模型',
                'verbose_name_plural': '機器學習模型列表',
            },
        ),
        migrations.CreateModel(
            name='ModelingJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='模型名稱')),
                ('description', models.CharField(max_length=100, verbose_name='模型敘述')),
                ('is_multi_label', models.BooleanField(verbose_name='是否為多標籤')),
                ('job_train_status', models.CharField(blank=True, choices=[('wait', '等待中'), ('processing', '處理中'), ('break', '中斷'), ('error', '錯誤'), ('done', '完成')], default='wait', max_length=20, null=True, verbose_name='任務狀態')),
                ('job_test_status', models.CharField(blank=True, choices=[('wait', '等待中'), ('processing', '處理中'), ('break', '中斷'), ('error', '錯誤'), ('done', '完成')], default='wait', max_length=20, null=True, verbose_name='任務狀態')),
                ('model_path', models.CharField(blank=True, max_length=100, verbose_name='模型存放位置')),
                ('jobRef', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='labeling_jobs.labelingjob')),
                ('model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='modeling_jobs.mlmodel')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accuracy', models.FloatField(blank=True, max_length=10, verbose_name='準確率')),
                ('report', models.CharField(max_length=1000, verbose_name='報告')),
                ('models_ref', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='modeling_jobs.modelingjob')),
            ],
        ),
    ]
