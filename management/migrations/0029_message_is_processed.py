# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-24 19:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0028_message_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_processed',
            field=models.BooleanField(default=False),
        ),
    ]
