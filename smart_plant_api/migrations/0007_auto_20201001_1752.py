# Generated by Django 3.0.8 on 2020-10-01 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_plant_api', '0006_remove_notificationsent_tokens'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overriderequest',
            name='request_time',
            field=models.DateTimeField(),
        ),
    ]
