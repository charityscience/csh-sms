# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-17 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0025_auto_20170727_1504'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='preg_signup',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contact',
            name='preg_update',
            field=models.NullBooleanField(default=False),
        ),
    ]
