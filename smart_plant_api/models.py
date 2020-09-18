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

class NotificationSent(models.Model):
    plant_id = models.CharField(max_length=32)
    reason = models.TextField()
    time = models.DateTimeField()

    def minutes_since_notification(self,current_time):
        return (current_time - self.time).seconds / 60