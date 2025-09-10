from django.db import models
from django.utils import timezone
import uuid
# Create your models here.
class ParkingSpot(models.Model):
    number = models.PositiveIntegerField(primary_key=True, unique=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Spot {self.number} - {'occupied' if self.is_occupied else 'free'}"
    
class CarEvent(models.Model):
    class Status(models.TextChoices):
        ENTERING = 'entering'
        PARKED = 'parked'
        LEAVING = 'leaving'
        HAS_LEFT = 'has_left'

    car_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license_plate = models.CharField(max_length=15)
    model = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=32, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    timestamp = models.DateTimeField(default=timezone.now)

    spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    occupied_spot_number = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.occupied_spot_number = self.spot.number if self.spot else None
        super().save(*args, **kwargs)
