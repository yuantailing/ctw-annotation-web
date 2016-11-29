# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-29 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ('direction', 'number')},
        ),
        migrations.AlterModelOptions(
            name='package',
            options={'ordering': ('direction', 'pk')},
        ),
        migrations.AlterField(
            model_name='image',
            name='package',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='collection.Package'),
        ),
        migrations.AlterField(
            model_name='userpackage',
            name='feedback',
            field=models.FileField(blank=True, upload_to='feedbacks/user_package'),
        ),
        migrations.AlterField(
            model_name='userpackage',
            name='upload',
            field=models.FileField(blank=True, upload_to='uploads/user_package'),
        ),
    ]
