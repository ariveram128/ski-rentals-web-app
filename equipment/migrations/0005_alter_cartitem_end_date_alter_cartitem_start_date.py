# Generated by Django 5.1.6 on 2025-03-29 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0004_equipment_hourly_rate_equipment_seasonal_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='end_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='start_date',
            field=models.DateTimeField(),
        ),
    ]
