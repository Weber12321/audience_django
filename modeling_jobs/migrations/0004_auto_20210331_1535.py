# Generated by Django 3.1.7 on 2021-03-31 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modeling_jobs', '0003_report'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='accuracy',
            field=models.FloatField(max_length=10, verbose_name='準確率'),
        ),
    ]
