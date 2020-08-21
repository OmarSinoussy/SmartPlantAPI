# Generated by Django 3.0.8 on 2020-08-21 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_plant_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OverrideRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plant_id', models.CharField(max_length=32)),
                ('request_time', models.DateTimeField()),
                ('lamp_intensity_state', models.IntegerField()),
                ('water_pump_state', models.BooleanField()),
            ],
        ),
    ]
