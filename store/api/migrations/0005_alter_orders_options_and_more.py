# Generated by Django 4.2.1 on 2023-05-11 22:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_orders_delivery_hours'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orders',
            options={'ordering': ['id', 'weight', 'regions', 'cost', 'complete_time', 'courier'], 'verbose_name_plural': 'Orders'},
        ),
        migrations.RenameField(
            model_name='orders',
            old_name='completed_time',
            new_name='complete_time',
        ),
    ]