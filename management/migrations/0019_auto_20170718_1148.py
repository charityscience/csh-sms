# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-18 18:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0018_auto_20170718_1040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='last_contacted',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='last_heard_from',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
