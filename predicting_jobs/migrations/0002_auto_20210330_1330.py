# Generated by Django 3.1.7 on 2021-03-30 05:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modeling_jobs', '0002_auto_20210326_1740'),
        ('predicting_jobs', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='predictingjob',
            name='apply_models',
        ),
        migrations.CreateModel(
            name='ApplyModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField(default=0)),
                ('modeling_jobs', models.ManyToManyField(blank=True, to='modeling_jobs.ModelingJob', verbose_name='使用模型列表')),
                ('predicting_jobs', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='predicting_jobs.predictingjob')),
            ],
            options={
                'verbose_name': '應用模型',
                'verbose_name_plural': '應用模型列表',
            },
        ),
    ]
