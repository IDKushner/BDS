# Generated by Django 4.2.1 on 2023-05-09 21:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_couriers_options_orders'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='completed_time',
            field=models.CharField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='orders',
            name='courier',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='api.couriers'),
        ),
    ]
