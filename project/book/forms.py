# app/forms.py
from django import forms
from .models import Booking, TripLeg, Location, TIME_CHOICES

def _locations():
    return Location.objects.all().order_by("name")

class BookingForm(forms.ModelForm):
    # Leg choices
    pickup_location_1 = forms.ModelChoiceField(_locations(), required=True, label="Pickup Location")
    dropoff_location_1 = forms.ModelChoiceField(_locations(), required=True, label="Dropoff Location")
    pickup_location_2 = forms.ModelChoiceField(_locations(), required=False, label="Return Pickup Location")
    dropoff_location_2 = forms.ModelChoiceField(_locations(), required=False, label="Return Dropoff Location")

    # Addresses per leg
    pickup_address_1 = forms.CharField(required=False, label="Pickup Address (optional)")
    dropoff_address_1 = forms.CharField(required=False, label="Dropoff Address (optional)")
    pickup_address_2 = forms.CharField(required=False, label="Return Pickup Address (optional)")
    dropoff_address_2 = forms.CharField(required=False, label="Return Dropoff Address (optional)")

    # Passengers (pricing tiers)
    passengers = forms.IntegerField(min_value=1, max_value=8, initial=1, required=True, label="Passengers")

    # Step 2 stored details
    adults   = forms.IntegerField(min_value=1, initial=1)
    children = forms.IntegerField(min_value=0, initial=0, required=False)
    luggage  = forms.IntegerField(min_value=0, initial=0, required=False)

    class Meta:
        model = Booking
        fields = [
            "trip_type", "transport_type",
            "pickup_time", "return_time",
            # keep summary addresses (optional)
            "pickup_address", "dropoff_address",
            "first_name", "last_name", "email", "country_code", "phone",
            "promo_code", "notes",
            "adults", "children", "luggage", "booster_seats", "flight_number",
            "checkin_date", "checkout_date",
        ]
        widgets = {
            "trip_type": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "transport_type": forms.RadioSelect(attrs={"class": "form-check-input"}),
            # Add form-control class to text inputs, date fields, and select fields
            "pickup_address": forms.TextInput(attrs={"class": "form-control"}),
            "dropoff_address": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "country_code": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "promo_code": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control"}),
            "adults": forms.NumberInput(attrs={"class": "form-control"}),
            "children": forms.NumberInput(attrs={"class": "form-control"}),
            "luggage": forms.NumberInput(attrs={"class": "form-control"}),
            "booster_seats": forms.NumberInput(attrs={"class": "form-control"}),
            "flight_number": forms.TextInput(attrs={"class": "form-control"}),
            "checkin_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "checkout_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pickup_time"].choices = [("", "— Select time —")] + TIME_CHOICES
        self.fields["return_time"].choices = [("", "— Select time —")] + TIME_CHOICES

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("trip_type") == "Round Trip":
            if not cleaned.get("pickup_location_2"):
                self.add_error("pickup_location_2", "Required for round trip.")
            if not cleaned.get("dropoff_location_2"):
                self.add_error("dropoff_location_2", "Required for round trip.")
            if not cleaned.get("return_time"):
                self.add_error("return_time", "Return time is required for round trip.")
        return cleaned

class TripLegForm(forms.ModelForm):
    class Meta:
        model = TripLeg
        fields = ["pickup_location", "dropoff_location", "sequence", "pickup_address", "dropoff_address"]
