# Generated by Django 4.2.5 on 2024-09-01 11:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_load', '0005_alter_ffwcrainfallstations_options'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='ffwcrainfallstations',
            table='ffwc_rainfall_stations_old',
        ),
    ]
