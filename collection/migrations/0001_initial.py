# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-06 12:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.IntegerField(db_index=True, default=None)),
                ('number', models.CharField(db_index=True, default=None, max_length=64)),
            ],
            options={
                'ordering': ('direction', 'number'),
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.IntegerField(db_index=True, default=None)),
            ],
            options={
                'ordering': ('direction', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='UserPackage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload', models.BinaryField(default=None, null=True)),
                ('feedback', models.TextField(blank=True)),
                ('statistics', models.TextField(blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='collection.Package')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='package',
            name='users',
            field=models.ManyToManyField(through='collection.UserPackage', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='image',
            name='package',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='collection.Package'),
        ),
        migrations.AlterUniqueTogether(
            name='userpackage',
            unique_together=set([('user', 'package')]),
        ),
        migrations.AlterUniqueTogether(
            name='image',
            unique_together=set([('direction', 'number')]),
        ),
    ]
