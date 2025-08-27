# app/forms.py
from django import forms
from .models import Booking, Location, TIME_CHOICES


def _locations():
    """Helper to provide an ordered queryset of locations for form fields."""
    return Location.objects.all().order_by("name")


class BookingForm(forms.ModelForm):
    """
    FIX: This form is now structured to correctly handle all user inputs for a multi-step process.
    - Removed redundant/conflicting fields from Meta (e.g., pickup_address).
    - All location and address fields are now custom fields, processed cleanly in the view.
    - Removed the extra 'passengers' field to rely solely on 'adults' and 'children'.
    """

    # --- Custom fields for Step 1 & 2 ---

    # Leg 1 (Outbound)
    pickup_location_1 = forms.ModelChoiceField(queryset=_locations(), required=True, label="Pickup Location")
    dropoff_location_1 = forms.ModelChoiceField(queryset=_locations(), required=True, label="Dropoff Location")
    pickup_address_1 = forms.CharField(required=False, label="Pickup Address (optional)")
    dropoff_address_1 = forms.CharField(required=False, label="Dropoff Address (optional)")

    # Leg 2 (Return)
    pickup_location_2 = forms.ModelChoiceField(queryset=_locations(), required=False, label="Return Pickup Location")
    dropoff_location_2 = forms.ModelChoiceField(queryset=_locations(), required=False, label="Return Dropoff Location")
    pickup_address_2 = forms.CharField(required=False, label="Return Pickup Address (optional)")
    dropoff_address_2 = forms.CharField(required=False, label="Return Dropoff Address (optional)")

    class Meta:
        model = Booking
        # These are the fields that are directly saved to the Booking model from the form.
        fields = [
            "trip_type", "transport_type",
            "pickup_time", "return_time",
            "first_name", "last_name", "email", "country_code", "phone",
            "promo_code", "notes",
            "adults", "children", "luggage", "booster_seats", "flight_number",
            "checkin_date", "checkout_date",
        ]
        widgets = {
            "trip_type": forms.RadioSelect(),
            "transport_type": forms.RadioSelect(),
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "email": forms.EmailInput(),
            "country_code": forms.TextInput(),
            "phone": forms.TextInput(),
            "promo_code": forms.TextInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "adults": forms.NumberInput(attrs={"min": 1, "value": 1}),
            "children": forms.NumberInput(attrs={"min": 0, "value": 0}),
            "luggage": forms.NumberInput(attrs={"min": 0, "value": 0}),
            "booster_seats": forms.NumberInput(attrs={"min": 0, "value": 0}),
            "flight_number": forms.TextInput(),
            "checkin_date": forms.DateInput(attrs={"type": "date"}),
            "checkout_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_time": forms.Select(),
            "return_time": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a placeholder to the time choice fields for better UX
        self.fields["pickup_time"].choices = [("", "— Select time —")] + TIME_CHOICES
        self.fields["return_time"].choices = [("", "— Select time —")] + TIME_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("trip_type") == "Round Trip":
            if not cleaned_data.get("pickup_location_2"):
                self.add_error("pickup_location_2", "Return pickup location is required for a round trip.")
            if not cleaned_data.get("dropoff_location_2"):
                self.add_error("dropoff_location_2", "Return dropoff location is required for a round trip.")
            if not cleaned_data.get("return_time"):
                self.add_error("return_time", "Return time is required for a round trip.")
        return cleaned_data
