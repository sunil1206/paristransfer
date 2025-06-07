from django import forms
from .models import Booking  # Make sure you import your Booking model

# class BookingForm(forms.ModelForm):
#     promo_code = forms.CharField(max_length=50, required=False)
#
#     class Meta:
#         model = Booking
#         fields = [
#             'trip_type', 'pickup_location', 'dropoff_location', 'transport_type',
#             'adults', 'children', 'luggage', 'pickup_time', 'return_time',
#             'first_name', 'last_name', 'email', 'country_code', 'phone',
#             'notes', 'promo_code'
#         ]

from django import forms
from .models import Booking

from django import forms
from .models import Booking

# class BookingForm(forms.ModelForm):
#     promo_code_input = forms.CharField(
#         max_length=50,
#         required=False,
#         label="Promo Code",
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter Promo Code (optional)',
#             'style': 'background-color: white; font-size: 15px; line-height: 28px; padding: 17px 49px 17px 20px; color: #055fa0;'
#         })
#     )
#
#     class Meta:
#         model = Booking
#         exclude = ['created_at', 'promo_code', 'price']
#
#         common_style = 'background-color: white; font-size: 15px; line-height: 28px; padding: 17px 49px 17px 20px; color: #055fa0;'
#
#         widgets = {
#             'trip_type': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
#             'pickup_location': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
#             'pickup_address': forms.TextInput(attrs={'class': 'form-control', 'style': common_style, 'placeholder': 'Custom Pickup Address (if Other)'}),
#             'dropoff_location': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
#             'dropoff_address': forms.TextInput(attrs={'class': 'form-control', 'style': common_style, 'placeholder': 'Custom Dropoff Address (if Other)'}),
#             'transport_type': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
#             'adults': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': common_style}),
#             'children': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
#             'luggage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
#             'pickup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'style': common_style}),
#             'return_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'style': common_style}),
#             'checkout_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': common_style}),
#             'checkin_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': common_style}),
#             'flight_number': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
#             'booster_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
#             'first_name': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
#             'last_name': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
#             'email': forms.EmailInput(attrs={'class': 'form-control', 'style': common_style}),
#             'country_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+33', 'style': common_style}),
#             'phone': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
#             'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': common_style}),
#         }


class BookingForm(forms.ModelForm):
    promo_code_input = forms.CharField(
        max_length=50,
        required=False,
        label="Promo Code",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Promo Code (optional)',
            'style': 'background-color: white; font-size: 15px; line-height: 28px; padding: 17px 49px 17px 20px; color: #055fa0;'
        })
    )

    # Optional Fields (override required=False if not needed in UI)


    class Meta:
        model = Booking
        exclude = ['created_at', 'promo_code', 'price']

        common_style = 'background-color: white; font-size: 15px; line-height: 28px; padding: 17px 49px 17px 20px; color: #055fa0;'

        widgets = {
            'trip_type': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
            'pickup_location': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
            'pickup_address': forms.TextInput(attrs={'class': 'form-control', 'style': common_style, 'placeholder': 'Custom Pickup Address (if Other)'}),
            'dropoff_location': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
            'dropoff_address': forms.TextInput(attrs={'class': 'form-control', 'style': common_style, 'placeholder': 'Custom Dropoff Address (if Other)'}),
            'transport_type': forms.Select(attrs={'class': 'form-control', 'style': common_style}),
            'adults': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': common_style}),
            'children': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
            'luggage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
            'pickup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'style': common_style}),
            'return_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'style': common_style}),
            'checkout_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': common_style}),
            'checkin_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': common_style}),
            'flight_number': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
            'booster_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'style': common_style}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'style': common_style}),
            'country_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+33', 'style': common_style}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'style': common_style}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': common_style}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default values via initial
        self.fields['trip_type'].initial = 'One Way'
        self.fields['transport_type'].initial = 'Car'
        self.fields['adults'].initial = 1
        self.fields['children'].initial = 0
        self.fields['luggage'].initial = 0
        self.fields['country_code'].initial = '+33'
