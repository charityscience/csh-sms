# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-05 17:24
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0004_contact_delay_in_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='functional_date_of_birth',
            field=models.DateField(blank=True, default=datetime.date.today),
        ),
    ]
