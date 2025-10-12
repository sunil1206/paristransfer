from django import forms
from .models import Booking, Location


class TimeInput(forms.TimeInput):
    """Custom widget to render a time input field."""
    input_type = 'time'


class DateInput(forms.DateInput):
    """Custom widget to render a date input field."""
    input_type = 'date'


class BookingForm(forms.ModelForm):
    """
    Form for creating a new booking.

    This form includes non-model fields (e.g., pickup_location_1) that are used by the
    template's JavaScript to handle the conditional logic for location selection.
    The final selected location IDs are passed to these fields for validation.
    """
    # These fields are not on the Booking model but are required for the form's
    # multi-step location selection logic in the template.
    pickup_location_1 = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=True,
        label="Pickup Location"
    )
    dropoff_location_1 = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=True,
        label="Dropoff Location"
    )
    pickup_location_2 = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label="Return Pickup Location"
    )
    dropoff_location_2 = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label="Return Dropoff Location"
    )

    # These fields correspond to the optional specific address inputs in the template.
    pickup_address_1 = forms.CharField(required=False)
    dropoff_address_1 = forms.CharField(required=False)
    pickup_address_2 = forms.CharField(required=False)
    dropoff_address_2 = forms.CharField(required=False)

    class Meta:
        model = Booking
        # These are the fields that directly map to the Booking model.
        fields = [
            'trip_type', 'transport_type', 'adults', 'children', 'luggage',
            'pickup_time', 'return_time', 'checkin_date', 'checkout_date',
            'flight_number', 'booster_seats', 'first_name', 'last_name',
            'email', 'country_code', 'phone', 'promo_code', 'notes', 'baby_seats'
        ]
        # Use custom widgets for a better user experience with date/time pickers.
        widgets = {
            'pickup_time': TimeInput(),
            'return_time': TimeInput(),
            'checkin_date': DateInput(attrs={'class': 'form-input'}),
            'checkout_date': DateInput(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            # The radio buttons are styled in the template, so no special widget is needed here.
            'trip_type': forms.RadioSelect,
            'transport_type': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We handle the location dropdowns dynamically in the template.
        # Setting the queryset here ensures that the form can validate the submitted ID.
        self.fields['pickup_location_1'].queryset = Location.objects.all()
        self.fields['dropoff_location_1'].queryset = Location.objects.all()
        self.fields['pickup_location_2'].queryset = Location.objects.all()
        self.fields['dropoff_location_2'].queryset = Location.objects.all()
