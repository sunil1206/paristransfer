# app/models.py
from typing import Optional, Tuple
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
import requests

TRIP_TYPE_CHOICES = [("One Way", "One Way"), ("Round Trip", "Round Trip")]
TRANSPORT_TYPE_CHOICES = [("Car", "Car"), ("Van", "Van")]
TIME_CHOICES = [("0", "Between 10 PM - 6 AM"), ("1", "Between 6 AM - 10 PM")]

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    class Meta: ordering = ("name",)
    def __str__(self): return self.name

class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)
    class Meta: ordering = ("-active", "-valid_until")
    def __str__(self): return f"{self.code} ({self.discount_percentage}%)"

class PricingRule(models.Model):
    name = models.CharField(max_length=100, default="Night Surcharge")
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    night_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # set if you want
    # IMPORTANT: your table already encodes pax tier prices; keep extra_per_passenger at 0
    extra_per_passenger_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    class Meta: ordering = ("-active", "name")
    def __str__(self): return f"{self.name} ({'Active' if self.active else 'Inactive'})"

class PriceMatrix(models.Model):
    """
    Passenger-tiered route prices.
    - For One Way: direction matters (origin -> destination).
    - For Round Trip: route is symmetric (origin < destination enforced).
    """
    origin = models.ForeignKey(Location, related_name="price_origin", on_delete=models.CASCADE)
    destination = models.ForeignKey(Location, related_name="price_destination", on_delete=models.CASCADE)
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES)
    # Optional; keep if rates ever differ by vehicle. If not used, set both to same values.
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPE_CHOICES, default="Car")
    pax_min = models.PositiveIntegerField(default=1)
    pax_max = models.PositiveIntegerField(default=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        indexes = [
            models.Index(fields=["origin", "destination", "trip_type", "transport_type"]),
            models.Index(fields=["pax_min", "pax_max"]),
        ]
        unique_together = ("origin", "destination", "trip_type", "transport_type", "pax_min", "pax_max")
        ordering = ("origin__name", "destination__name", "trip_type", "transport_type", "pax_min")

    def save(self, *args, **kwargs):
        # Enforce undirected storage for Round Trip (origin id < destination id)
        if self.trip_type == "Round Trip" and self.origin_id and self.destination_id:
            if self.origin_id > self.destination_id:
                self.origin_id, self.destination_id = self.destination_id, self.origin_id
        super().save(*args, **kwargs)

    def __str__(self):
        rng = f"{self.pax_min}-{self.pax_max}"
        return f"{self.trip_type}: {self.origin} ↔ {self.destination} [{self.transport_type}] ({rng}) → €{self.price}"

class Booking(models.Model):
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default="One Way")
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPE_CHOICES, default="Car")

    # Summary of leg 1 for admin
    pickup_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='pickup_bookings')
    dropoff_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='dropoff_bookings')

    # (Kept for quick view, pricing uses TripLeg addresses now)
    pickup_address = models.CharField(max_length=255, blank=True, null=True)
    dropoff_address = models.CharField(max_length=255, blank=True, null=True)
    pickup_latitude = models.FloatField(blank=True, null=True)
    pickup_longitude = models.FloatField(blank=True, null=True)
    dropoff_latitude = models.FloatField(blank=True, null=True)
    dropoff_longitude = models.FloatField(blank=True, null=True)

    adults = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    children = models.PositiveIntegerField(default=0)
    luggage = models.PositiveIntegerField(default=0)

    pickup_time = models.CharField(max_length=20, choices=TIME_CHOICES, blank=True)  # for leg 1
    return_time = models.CharField(max_length=20, choices=TIME_CHOICES, blank=True)  # for leg 2

    checkin_date = models.DateField(blank=True, null=True)
    checkout_date = models.DateField(blank=True, null=True)

    flight_number = models.CharField(max_length=20, blank=True, null=True)
    booster_seats = models.PositiveIntegerField(default=0)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    country_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=15)

    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ("-created_at",)
    def __str__(self): return f"{self.first_name} {self.last_name} - {self.trip_type}"

    def total_passengers(self, passengers_override: Optional[int] = None) -> int:
        return int(passengers_override) if passengers_override is not None else int(self.adults or 0) + int(self.children or 0)

    def apply_discount(self, total_price: float) -> float:
        if (self.promo_code and self.promo_code.active and
            self.promo_code.valid_from <= timezone.now() <= self.promo_code.valid_until):
            discount = (self.promo_code.discount_percentage / 100) * total_price
            return round(total_price - float(discount), 2)
        return round(float(total_price), 2)

    def calculate_total_price(self, passengers_override: Optional[int] = None) -> float:
        """
        Uses PriceMatrix tiered prices, applies night charge per leg if configured,
        then promo. No extra-per-passenger add-on because tiers already encode pax pricing.
        """
        pax = self.total_passengers(passengers_override)
        total = 0.0

        # If RT with reverse leg, try Round Trip matrix; else sum OW legs
        legs = list(self.legs.all().order_by("sequence"))
        if self.trip_type == "Round Trip" and len(legs) == 2:
            l1, l2 = legs
            reverse = (l1.pickup_location_id == l2.dropoff_location_id and
                       l1.dropoff_location_id == l2.pickup_location_id)
            if reverse:
                total += find_matrix_price("Round Trip", self.transport_type,
                                           l1.pickup_location_id, l1.dropoff_location_id, pax)
            else:
                total += find_matrix_price("One Way", self.transport_type,
                                           l1.pickup_location_id, l1.dropoff_location_id, pax)
                total += find_matrix_price("One Way", self.transport_type,
                                           l2.pickup_location_id, l2.dropoff_location_id, pax)
        else:
            for leg in legs:
                total += find_matrix_price("One Way", self.transport_type,
                                           leg.pickup_location_id, leg.dropoff_location_id, pax)

        # Night charges
        rule = PricingRule.objects.filter(active=True).first()
        night_charge = float(rule.night_charge) if rule else 0.0
        if night_charge > 0:
            if self.pickup_time == "0":  # night for leg 1
                total += night_charge
            if self.trip_type == "Round Trip" and self.return_time == "0":
                total += night_charge

        total = self.apply_discount(total)
        self.price = total
        self.save(update_fields=["price"])
        return total

    def save(self, *args, **kwargs):
        # Keep quick geocode for summary addresses if present
        if self.pickup_address and not self.pickup_latitude:
            latlng = get_latlng_from_address(self.pickup_address)
            if latlng != (None, None):
                self.pickup_latitude, self.pickup_longitude = latlng
        if self.dropoff_address and not self.dropoff_latitude:
            latlng = get_latlng_from_address(self.dropoff_address)
            if latlng != (None, None):
                self.dropoff_latitude, self.dropoff_longitude = latlng
        super().save(*args, **kwargs)

class TripLeg(models.Model):
    booking = models.ForeignKey(Booking, related_name="legs", on_delete=models.CASCADE)
    pickup_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tripleg_pickups')
    dropoff_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tripleg_dropoffs')
    sequence = models.PositiveIntegerField(default=1)

    # NEW: per-leg addresses (visible in admin & used if you want per-leg geocoding later)
    pickup_address = models.CharField(max_length=255, blank=True, null=True)
    dropoff_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ("booking", "sequence")
        indexes = [
            models.Index(fields=["booking", "sequence"]),
            models.Index(fields=["pickup_location", "dropoff_location"]),
        ]
    def __str__(self): return f"Leg {self.sequence}: {self.pickup_location} → {self.dropoff_location}"

# --- Pricing lookup helper ---
def find_matrix_price(trip_type: str, transport_type: str, origin_id: int, destination_id: int, pax: int) -> float:
    qs = PriceMatrix.objects.filter(
        trip_type=trip_type,
        transport_type=transport_type,
        pax_min__lte=pax, pax_max__gte=pax
    )
    if trip_type == "One Way":
        row = qs.filter(origin_id=origin_id, destination_id=destination_id).first()
    else:
        a, b = sorted([origin_id, destination_id])
        row = qs.filter(origin_id=a, destination_id=b).first()
    return float(row.price) if row else 0.0

# --- Google Geocoding (optional) ---
def get_latlng_from_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
    if not api_key: return None, None
    try:
        resp = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': address, 'key': api_key},
            timeout=8
        )
        data = resp.json()
        if data.get('status') == 'OK':
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception:
        pass
    return None, None
