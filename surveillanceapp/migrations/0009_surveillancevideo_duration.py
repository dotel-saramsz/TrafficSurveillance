# Generated by Django 2.0.7 on 2018-07-27 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveillanceapp', '0008_surveillancevideo_thumbnail_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveillancevideo',
            name='duration',
            field=models.BigIntegerField(null=True),
        ),
    ]
