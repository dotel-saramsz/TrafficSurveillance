# Generated by Django 2.0.7 on 2018-08-03 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveillanceapp', '0015_auto_20180731_0940'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveillancevideo',
            name='last_analysed',
            field=models.DateTimeField(null=True),
        ),
    ]
