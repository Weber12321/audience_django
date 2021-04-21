# Generated by Django 3.1.8 on 2021-04-20 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labeling_jobs', '0007_auto_20210420_1648'),
        ('modeling_jobs', '0006_remove_evalprediction_ground_truth_labels'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evalprediction',
            options={'verbose_name': '驗證標記', 'verbose_name_plural': '驗證標記列表'},
        ),
        migrations.AlterField(
            model_name='evalprediction',
            name='prediction_labels',
            field=models.ManyToManyField(to='labeling_jobs.Label', verbose_name='預測標籤'),
        ),
    ]
