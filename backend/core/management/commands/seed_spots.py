from django.core.management.base import BaseCommand
from core.models import ParkingSpot

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for i in range(1, 26):
            ParkingSpot.objects.get_or_create(number=n, defaults={'is_occupied': False})
        self.stdout.write(self.style.SUCCESS('Successfully seeded 25 parking spots.'))