# Generated by Django 3.1.13 on 2021-07-23 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('labeling_jobs', '0002_auto_20210723_1719'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rule',
            old_name='job',
            new_name='labeling_job',
        ),
    ]
