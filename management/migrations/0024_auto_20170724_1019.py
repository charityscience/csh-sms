# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-24 17:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0023_auto_20170724_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='preferred_time',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
