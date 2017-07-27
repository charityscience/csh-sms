# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-24 17:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0022_contact_cancelled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='url_information',
        ),
        migrations.AlterField(
            model_name='contact',
            name='city',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='district',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='division',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='gender',
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AlterField(
            model_name='contact',
            name='hospital_name',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='language_preference',
            field=models.CharField(default='English', max_length=20),
        ),
        migrations.AlterField(
            model_name='contact',
            name='method_of_sign_up',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='not_vaccinated_why',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='contact',
            name='org_sign_up',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='contact',
            name='religion',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='contact',
            name='state',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]