# Generated by Django 3.0.8 on 2020-08-26 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_plant_api', '0002_overriderequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overriderequest',
            name='request_time',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='readingentry',
            name='reading_date',
            field=models.DateField(),
        ),
    ]
