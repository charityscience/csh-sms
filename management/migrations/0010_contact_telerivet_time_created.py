# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-05 17:59
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0009_auto_20170705_1055'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='telerivet_time_created',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
