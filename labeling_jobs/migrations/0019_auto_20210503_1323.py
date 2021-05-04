# Generated by Django 3.1.8 on 2021-05-03 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labeling_jobs', '0018_auto_20210503_1322'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rule',
            name='label',
        ),
        migrations.AddField(
            model_name='rule',
            name='labels',
            field=models.ManyToManyField(to='labeling_jobs.Label', verbose_name='標籤'),
        ),
    ]