# Generated by Django 5.1.6 on 2025-03-31 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0006_equipment_equipment_subtype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='equipment_subtype',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
