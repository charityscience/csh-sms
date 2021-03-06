# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-05 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0007_contact_contact_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='children_previously_vaccinated',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='contact',
            name='city',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='district',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='division',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='doctor_name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contact',
            name='hospital_name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contact',
            name='method_of_sign_up',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='monthly_income_rupees',
            field=models.IntegerField(blank=True, default=999999),
        ),
        migrations.AddField(
            model_name='contact',
            name='mother_first_name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contact',
            name='mother_last_name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contact',
            name='not_vaccinated_why',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='contact',
            name='org_sign_up',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='religion',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='state',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='telerivet_contact_id',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='contact',
            name='telerivet_sender_phone',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='contact',
            name='trial_group',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='trial_id',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='contact',
            name='url_information',
            field=models.URLField(blank=True),
        ),
    ]
