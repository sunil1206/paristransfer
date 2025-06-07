from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.code
#
# class Booking(models.Model):
#     trip_type = models.CharField(max_length=20)
#     pickup_location = models.CharField(max_length=50)
#     dropoff_location = models.CharField(max_length=50)
#     transport_type = models.CharField(max_length=20)
#     adults = models.IntegerField()
#     children = models.IntegerField()
#     luggage = models.IntegerField()
#     pickup_time = models.CharField(max_length=5,blank=True)
#     return_time = models.CharField(max_length=5,blank=True)
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     email = models.EmailField()
#     country_code = models.CharField(max_length=5)
#     phone = models.CharField(max_length=15)
#     notes = models.TextField(blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True)

from django.db import models
from django.db import models

from django.db import models

from django.db import models
from django.utils import timezone

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class Booking(models.Model):
    TRIP_TYPE_CHOICES = [
        ("One Way", "One Way"),
        ("Round Trip", "Round Trip"),
    ]

    TRANSPORT_TYPE_CHOICES = [
        ("Car", "Car"),
        ("Van", "Van"),
    ]

    LOCATION_CHOICES = [
        ("BEAUVAIS", "BEAUVAIS"),
        ("Bayeux", "Bayeux"),
        ("CDG(Charles de Gaulle Airport)", "CDG(Charles de Gaulle Airport)"),
        ("Fontainebleau", "Fontainebleau"),
        ("ORLY (Orly Airport)", "ORLY (Orly Airport)"),
        ("Paris hotels / Train Stations", "Paris hotels / Train Stations"),
        ("Reims", "Reims"),
        ("CDG", "CDG"),
        ("Disneyland", "Disneyland"),
        ("Other", "Other"),
    ]

    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES,default="One Way")
    pickup_location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    dropoff_location = models.CharField(max_length=50, choices=LOCATION_CHOICES)

    pickup_address = models.CharField(max_length=255, blank=True, null=True)
    dropoff_address = models.CharField(max_length=255, blank=True, null=True)
    pickup_latitude = models.FloatField(blank=True, null=True)
    pickup_longitude = models.FloatField(blank=True, null=True)
    dropoff_latitude = models.FloatField(blank=True, null=True)
    dropoff_longitude = models.FloatField(blank=True, null=True)

    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPE_CHOICES, default="Car")
    adults = models.IntegerField()
    children = models.IntegerField()
    luggage = models.IntegerField()

    pickup_time = models.CharField(max_length=5, blank=True)
    return_time = models.CharField(max_length=5, blank=True)
    checkout_date = models.DateField(blank=True, null=True)
    checkin_date = models.DateField(blank=True, null=True)

    flight_number = models.CharField(max_length=20, blank=True, null=True)
    booster_seats = models.PositiveIntegerField(default=0)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    country_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=15)

    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.trip_type}"

    def apply_discount(self):
        if self.promo_code and self.promo_code.active and self.promo_code.valid_from <= timezone.now() <= self.promo_code.valid_until:
            discount = (self.promo_code.discount_percentage / 100) * self.price
            return round(self.price - discount, 2)
        return self.price



class TaxiData(models.Model):
    trip_type = models.CharField(max_length=100)
    pickup_location = models.CharField(max_length=100)
    dropoff_location = models.CharField(max_length=100)
    transport_type = models.CharField(max_length=100)
    adults = models.FloatField()
    children = models.FloatField()
    pickup_time = models.FloatField()
    return_time = models.FloatField()
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
