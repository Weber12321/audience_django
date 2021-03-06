# Generated by Django 3.1.13 on 2022-04-25 14:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentingJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Job', max_length=100, verbose_name='標記任務名稱')),
                ('description', models.TextField(verbose_name='定義與說明')),
                ('is_multi_label', models.BooleanField(default=False, verbose_name='是否屬於多標籤')),
                ('job_type', models.CharField(choices=[('machine_learning_task', '監督式學習模型'), ('rule_task', '關鍵字與規則模型')], default='rule_task', max_length=100, verbose_name='任務類型')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='最後修改時間')),
                ('create_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '資料整備工作',
                'verbose_name_plural': '資料整備工作列表',
            },
        ),
    ]
