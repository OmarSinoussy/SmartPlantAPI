from django.db import models

class ReadingEntry(models.Model):
    plant_id = models.CharField(max_length=32)
    reading_date = models.DateField()

    soil_moisture_reading = models.IntegerField()
    light_intensity_reading = models.IntegerField()
    water_level_reading = models.IntegerField()

class OverrideRequest(models.Model):
    plant_id = models.CharField(max_length=32)
    request_time = models.DateField()

    lamp_intensity_state = models.IntegerField()
    water_pump_state = models.BooleanField()

class TokenPlantIDBind(models.Model):
    plant_id = models.CharField(max_length=32)
    tokens = models.TextField()