from ninja import NinjaAPI, Schema
from core.models import ParkingSpot, CarEvent
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models.functions import Extract
from django.db.models import Q, F, Min, ExpressionWrapper, Sum, DurationField, FloatField
import random, string, datetime

api = NinjaAPI()
RATE_PER_SECOND = 0.03

# Schemas
class SpotOut(Schema):
    number: int
    is_occupied: bool

class CarEventOut(Schema):
    car_uuid: str
    license_plate: str
    model: Optional[str]
    color: Optional[str]
    year: Optional[int]
    status: str
    timestamp: datetime.datetime
    spot_number: Optional[int]
    occupied_spot_number: Optional[int]

class SessionOut(Schema):
    car_uuid: str
    license_plate: str
    start: datetime.datetime
    end: datetime.datetime
    seconds: int
    cost: float

class StateOut(Schema):
    spots: List[SpotOut]
    entering: List[CarEventOut]
    parked: List[CarEventOut]
    leaving: List[CarEventOut]
    history: List[CarEventOut]
    occupancy_percent: float
    occupancy_label: str
    counts: dict
    finished_sessions: List[SessionOut]

class EnterCarIn(Schema):
    license_plate: str
    model: Optional[str] = ""
    color: Optional[str] = ""
    year: Optional[int] = None

# Helpers
def random_plate():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}-{numbers}"

def random_car_fields():
    models = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'BMW', 'Mercedes', 'Volkswagen']
    colors = ['Rojo', 'Azul', 'Verde', 'Negro', 'Blanco', 'Plateado', 'Amarillo']
    years = list(range(1990, 2026))
    return {
        "license_plate": random_plate(),
        "model": random.choice(models),
        "color": random.choice(colors),
        "year": random.choice(years)
    }

def compute_occupancy_label(pct: float) -> str:
    if pct >= 100:
        return "full"
    if pct < 50:
        return "available"
    return "halffull"

def get_total_cash() -> float:
    qs = (
        CarEvent.objects
        .filter(status__in=[CarEvent.Status.ENTERING, CarEvent.Status.HAS_LEFT])
        .values('car_uuid', 'license_plate')
        .annotate(
            start_time=Min('timestamp', filter=Q(status=CarEvent.Status.ENTERING)),
            end_time=Min('timestamp', filter=Q(status=CarEvent.Status.HAS_LEFT)),
        )
        .exclude(start_time=None)
        .exclude(end_time=None)
        .annotate(
            duration=ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=DurationField()
            )
        )
        .annotate(
            seconds=ExpressionWrapper(
                        Extract(F('duration'), 'epoch'),  # converts timedelta to seconds
                output_field=FloatField()
            ),
            cost=ExpressionWrapper(
                F('seconds') * RATE_PER_SECOND,
                output_field=FloatField()
            )
        )
        .aggregate(total_cash=Sum('cost'))
    )
    total = qs['total_cash'] or 0
    return round(float(total), 2)

def get_state_payload() -> StateOut:
    spots_qs = ParkingSpot.objects.all().order_by('number')
    spots = [{'number': s.number, 'is_occupied': s.is_occupied} for s in spots_qs]
    total_spots = len(spots) or 1
    occupied = sum(1 for s in spots if s['is_occupied'])
    pct = (occupied / total_spots) * 100

    history_qs = CarEvent.objects.order_by('-timestamp')[:200]
    history = [
        CarEventOut(
            car_uuid=str(e.car_uuid),
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=e.status,
            timestamp=e.timestamp,
            occupied_spot_number=e.occupied_spot_number
        )
        for e in history_qs
    ]

    # latest status per car
    latest_ids = (
        CarEvent.objects
        .order_by('car_uuid', '-timestamp')
        .distinct('car_uuid')
        .values_list('car_uuid', flat=True)
    )
    latest = CarEvent.objects.filter(car_uuid__in=latest_ids)

    entering = [
        CarEventOut(
            car_uuid=str(e.car_uuid),
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=e.status,
            timestamp=e.timestamp,
            occupied_spot_number=e.occupied_spot_number
        )
        for e in latest if e.status == CarEvent.Status.ENTERING
    ]

    parked = [
        CarEventOut(
            car_uuid=str(e.car_uuid),
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=e.status,
            timestamp=e.timestamp,
            occupied_spot_number=e.occupied_spot_number
        )
        for e in latest if e.status == CarEvent.Status.PARKED
    ]

    leaving = [
        CarEventOut(
            car_uuid=str(e.car_uuid),
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=e.status,
            timestamp=e.timestamp,
            occupied_spot_number=e.occupied_spot_number
        )
        for e in latest if e.status == CarEvent.Status.LEAVING
    ]

    # finished sessions
    sessions = []
    left_latest_ids = (
        CarEvent.objects.filter(status=CarEvent.Status.HAS_LEFT)
        .order_by('car_uuid', '-timestamp')
        .distinct('car_uuid')
        .values_list('car_uuid', flat=True)
    )
    for cid in left_latest_ids:
        start = CarEvent.objects.filter(car_uuid=cid, status=CarEvent.Status.ENTERING).order_by('timestamp', '-car_uuid').first()
        end = CarEvent.objects.filter(car_uuid=cid, status=CarEvent.Status.HAS_LEFT).order_by('-timestamp', '-car_uuid').first()
        if not start or not end:
            continue
        seconds = int((end.timestamp - start.timestamp).total_seconds())
        cost = round(seconds * RATE_PER_SECOND, 2)
        sessions.append(SessionOut(
            car_uuid=str(cid),
            license_plate=end.license_plate,
            start=start.timestamp,
            end=end.timestamp,
            seconds=seconds,
            cost=cost
        ))

    total_cash = get_total_cash()

    return StateOut(
        spots=[SpotOut(**s) for s in spots],
        entering=entering,
        parked=parked,
        leaving=leaving,
        history=history[::-1],
        occupancy_percent=pct,
        occupancy_label=compute_occupancy_label(pct),
        counts={
            "entering": len(entering),
            "parked": len(parked),
            "leaving": len(leaving),
            "total_cash": total_cash
        },
        finished_sessions=sessions,
    )

# Transaction logic
@transaction.atomic
def resolve_previous_cycle():
    now = timezone.now()
    free_spots = list(ParkingSpot.objects.filter(is_occupied=False).order_by('number'))
    entering_latest = list(CarEvent.objects.raw(
        """SELECT DISTINCT ON (car_uuid) * FROM core_carevent WHERE status = %s ORDER BY car_uuid DESC, timestamp DESC""",
        [CarEvent.Status.ENTERING]
    ))
    for e in entering_latest:
        if not free_spots:
            CarEvent.objects.create(
                car_uuid=e.car_uuid,
                license_plate=e.license_plate,
                model=e.model,
                color=e.color,
                year=e.year,
                status=CarEvent.Status.LEAVING,
                timestamp=now,
            )
            continue
        spot = free_spots.pop(0)
        spot.is_occupied = True
        spot.save(update_fields=['is_occupied'])
        CarEvent.objects.create(
            car_uuid=e.car_uuid,
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=CarEvent.Status.PARKED,
            timestamp=now,
            occupied_spot_number=spot.number
        )

    leaving_latest = list(CarEvent.objects.raw(
        """SELECT DISTINCT ON (car_uuid) * FROM core_carevent WHERE status = %s ORDER BY car_uuid DESC, timestamp DESC""",
        [CarEvent.Status.LEAVING]
    ))
    for e in leaving_latest:
        if e.occupied_spot_number:
            ParkingSpot.objects.filter(number=e.occupied_spot_number).update(is_occupied=False)
        CarEvent.objects.create(
            car_uuid=e.car_uuid,
            license_plate=e.license_plate,
            model=e.model,
            color=e.color,
            year=e.year,
            status=CarEvent.Status.HAS_LEFT,
            timestamp=now,
        )

# API Endpoints
@api.post("/cycle")

def cycle(request):
    resolve_previous_cycle()

    roll = random.randint(0, 1)
    entering_count = random.randint(0, 3) if roll == 0 else 0

    parked_ids = (
        CarEvent.objects.filter(status=CarEvent.Status.PARKED)
        .order_by('car_uuid', '-timestamp')
        .distinct('car_uuid')
        .values_list('car_uuid', flat=True)
    )
    parked_latest = list(CarEvent.objects.filter(car_uuid__in=parked_ids))
    leaving_count = random.randint(1, min(3, len(parked_latest))) if roll == 1 else 0

    now = timezone.now()

    for _ in range(entering_count):
        fields = random_car_fields()
        CarEvent.objects.create(
            status=CarEvent.Status.ENTERING,
            timestamp=now,
            **fields
        )
    if leaving_count > 0:
        random.shuffle(parked_latest)
        for e in parked_latest[:leaving_count]:
            CarEvent.objects.create(
                car_uuid=e.car_uuid,
                license_plate=e.license_plate,
                model=e.model,
                color=e.color,
                year=e.year,
                status=CarEvent.Status.LEAVING,
                timestamp=now,
            )
    return {"ok": True, "entering_created": entering_count, "leaving_created": leaving_count}

@api.post("/cars/enter", response=CarEventOut)
def manual_enter(request, payload: EnterCarIn):
    e = CarEvent.objects.create(
        license_plate=payload.license_plate,
        model=payload.model or "",
        color=payload.color or "",
        year=payload.year,
        status=CarEvent.Status.ENTERING,
        timestamp=timezone.now(),
    )
    return CarEventOut(
        car_uuid=str(e.car_uuid),
        license_plate=e.license_plate,
        model=e.model,
        color=e.color,
        year=e.year,
        status=e.status,
        timestamp=e.timestamp,
        occupied_spot_number=e.occupied_spot_number
    )

@api.get("/state", response=StateOut)
def get_state(request):
    return get_state_payload()
