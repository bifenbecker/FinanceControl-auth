# Generated by Django 3.2.8 on 2022-03-28 16:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_auto_20220328_1806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refreshtoken',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2022, 3, 28, 16, 1, 5, 86625)),
        ),
        migrations.AlterField(
            model_name='refreshtoken',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 11, 16, 1, 5, 86625)),
        ),
    ]
