# Generated by Django 3.1.8 on 2021-05-28 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labeling_jobs', '0030_auto_20210514_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='s_area_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='來源網站'),
        ),
        migrations.AlterField(
            model_name='document',
            name='s_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='來源'),
        ),
    ]