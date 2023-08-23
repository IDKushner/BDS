# Generated by Django 4.2.1 on 2023-05-09 17:59

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Couriers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('courier_type', models.CharField(choices=[('FOOT', 'FOOT'), ('BIKE', 'BIKE'), ('AUTO', 'AUTO')], max_length=10)),
                ('regions', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), size=None)),
                ('working_hours', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=11), size=None)),
            ],
            options={
                'ordering': ['id', 'courier_type'],
            },
        ),
    ]
