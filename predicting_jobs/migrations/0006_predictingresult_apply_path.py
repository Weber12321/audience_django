# Generated by Django 3.1.8 on 2021-04-27 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predicting_jobs', '0005_remove_predictingresult_feature_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictingresult',
            name='apply_path',
            field=models.JSONField(null=True, verbose_name='模型預測路徑'),
        ),
    ]