# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-27 22:04
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0024_auto_20170724_1019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='alt_phone_number',
            field=models.CharField(default='012345', max_length=20, validators=[django.core.validators.RegexValidator(code='Invalid phone_number', message="Phone number must be entered in the format: '+9199999999'. Up to 15 digits allowed.", regex='^\\+?91?\\d{9,15}$')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone_number',
            field=models.CharField(default='012345', max_length=20, validators=[django.core.validators.RegexValidator(code='Invalid phone_number', message="Phone number must be entered in the format: '+9199999999'. Up to 15 digits allowed.", regex='^\\+?91?\\d{9,15}$')]),
        ),
    ]
