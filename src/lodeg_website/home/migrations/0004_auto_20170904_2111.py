# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-04 21:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_lodeguser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cache',
            fields=[('id', models.AutoField(
                auto_created=True, primary_key=True, serialize=False,
                verbose_name='ID')),
                ('data', models.BinaryField()), ],),
        migrations.AlterField(
            model_name='lodeguser', name='lodeg_user_id',
            field=models.CharField(max_length=100, unique=True),),
        migrations.AddField(
            model_name='cache', name='user', field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='home.LodegUser'),), ]
