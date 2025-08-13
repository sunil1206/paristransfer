import os
import pickle

import numpy as np
import joblib
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings

from .forms import BookingForm
from .models import Booking, PromoCode
from twilio.rest import Client  # For SMS notifications (optional)

# Load the trained ML model & encoders
price_model = joblib.load("booking/models/taxi_price_classifier.joblib")
label_encoders = joblib.load("booking/models/label_encoders.joblib")
# clf = joblib.load("booking/models/taxi_price_classifier.joblib")

# joblib.load("booking/models/label_encoders.joblib")

from django.db import models
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
import numpy as np
from django.conf import settings

import joblib
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse

# Load trained model and preprocessing tools
clf = joblib.load("booking/models/taxi_price_classifier.joblib")
scaler = joblib.load("booking/models/scaler.joblib")
label_encoders = joblib.load("booking/models/label_encoders.joblib")


def time_to_minutes(time_str):
    """Convert HH:MM time format to minutes."""
    if time_str:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    return 0


import os
import numpy as np
import joblib
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import Booking

# Load the trained model and label encoders
MODEL_PATH = os.path.join(settings.BASE_DIR, "booking/models/taxi_price_classifier.joblib")
LABEL_ENCODERS_PATH = os.path.join(settings.BASE_DIR, "booking/models/label_encoders.joblib")

# Load ML model
try:
    price_model = joblib.load(MODEL_PATH)
    label_encoders = joblib.load(LABEL_ENCODERS_PATH)
except Exception as e:
    price_model, label_encoders = None, None
    print(f"Error loading models: {e}")


def encode_label(feature, category):
    """Encodes categorical values using preloaded label encoders."""
    try:
        return label_encoders[category].transform([feature])[0]
    except KeyError:
        return 0  # Default value if encoding fails


def time_to_minutes(time_str):
    """Converts time (HH:MM) to total minutes."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except ValueError:
        return 0  # Default if format is incorrect


import os
import numpy as np
import joblib  # For loading .joblib models
from django.conf import settings
from django.shortcuts import render


def load_model(model_path):
    """Loads a machine learning model from a file."""
    full_path = os.path.join(settings.BASE_DIR, model_path)
    print(f"Loading model from: {full_path}")  # Debugging

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Model file not found: {full_path}")

    model = joblib.load(full_path)  # Using joblib instead of pickle
    return model


def get_float_value(request, key):
    """Safely extract a float value from POST data."""
    value = request.POST.get(key, "0")  # Default to "0" to prevent errors
    try:
        return float(value)
    except ValueError:
        return 0  # Return default if conversion fails


def predict_price(request):
    predicted_price = None
    if request.method == "POST":
        try:
            print("Received POST request with data:", request.POST)  # Debugging

            # Extract features from the form
            features = np.array([[
                get_float_value(request, "trip_type"),
                get_float_value(request, "pickup_location"),
                get_float_value(request, "dropoff_location"),
                get_float_value(request, "transport_type"),
                get_float_value(request, "adults"),
                get_float_value(request, "children"),
                # get_float_value(request, "luggage"),
                get_float_value(request, "pickup_time"),
                get_float_value(request, "return_time"),
            ]])

            # Load the trained model
            price_model = load_model('booking/models/price_model.joblib')

            print("Predicting with features:", features)  # Debugging
            predicted_price = round(price_model.predict(features)[0])

        except Exception as e:
            print(f"Error occurred: {e}")  # Debugging
            predicted_price = f"Error: {e}"

    return render(request, 'core/booking.html', {'predicted_price': predicted_price})


############################################################################################################

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import numpy as np
import joblib
import os

def load_model(model_path):
    """Loads a machine learning model from a file."""
    full_path = os.path.join(settings.BASE_DIR, model_path)
    print(f"Loading model from: {full_path}")  # Debugging

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Model file not found: {full_path}")

    model = joblib.load(full_path)  # Using joblib instead of pickle
    return model

def get_float_value(request, key):
    """Safely extract a float value from POST data."""
    value = request.POST.get(key, "0")  # Default to "0" to prevent errors
    try:
        return float(value)
    except ValueError:
        return 0  # Return default if conversion fails
def load_model(path):
    return joblib.load(path)
import os
import pandas as pd
import logging
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib import messages
from .forms import BookingForm
from .models import PromoCode


logger = logging.getLogger(__name__)

# -------------------------------
# Encoder dictionaries (for ML only)
# -------------------------------
PICKUP_LOCATION_ENCODER = {
    "BEAUVAIS": 0,
    "Bayeux": 1,
    "CDG(Charles de Gaulle Airport)": 2,
    "Fontainebleau": 3,
    "ORLY (Orly Airport)": 4,
    "Paris hotels / Train Stations": 5,
    "Reims": 6,
}

DROPOFF_LOCATION_ENCODER = {
    "BEAUVAIS": 0,
    "CDG": 1,
    "Disneyland": 2,
    "ORLY (Orly Airport)": 3,
    "Paris hotels / Train Stations": 4,
}

TRIP_TYPE_ENCODER = {
    "One Way": 0,
    "Round Trip": 1,
}

TRANSPORT_TYPE_ENCODER = {
    "Car": 0,
    "Van": 1,
}

# -------------------------------
# Utility Functions
# -------------------------------

def get_float_value(request, key):
    try:
        return float(request.POST.get(key, 0))
    except (TypeError, ValueError):
        return 0.0

def prepare_features(request):
    return {
        "trip_type": TRIP_TYPE_ENCODER.get(request.POST.get("trip_type"), 0),
        "pickup_location": PICKUP_LOCATION_ENCODER.get(request.POST.get("pickup_location"), 0),
        "dropoff_location": DROPOFF_LOCATION_ENCODER.get(request.POST.get("dropoff_location"), 0),
        "transport_type": TRANSPORT_TYPE_ENCODER.get(request.POST.get("transport_type"), 0),
        "adults": get_float_value(request, "adults"),
        "children": get_float_value(request, "children"),
        "pickup_time": get_float_value(request, "pickup_time"),
        "return_time": get_float_value(request, "return_time"),
    }

def predict_price(features_dict):
    model_path = os.path.join(settings.BASE_DIR, 'booking/models/price_model.joblib')
    model = load_model(model_path)
    df = pd.DataFrame([features_dict])
    return round(model.predict(df)[0], 2)

def apply_promo_code(promo_code, price):
    try:
        promo = PromoCode.objects.get(code=promo_code)
        if promo.valid_from <= timezone.now() <= promo.valid_until and promo.active:
            discount = (promo.discount_percentage / 100) * price
            return price - discount
    except PromoCode.DoesNotExist:
        pass
    return price

# def send_user_confirmation_email(booking, predicted_price):
#     subject = "Booking Confirmation – Your Ride is Booked!"
#     plain_message = f"Dear {booking.first_name}, your booking is confirmed. Fare: EUR {predicted_price}."
#     from_email = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [booking.email]
#     html_message = f"""
#     <html>
#       <body style="font-family: Arial; background-color: #f4f4f4; padding: 20px;">
#         <div style="max-width: 600px; background: white; padding: 30px; border-radius: 10px;">
#           <h2 style="color: #4CAF50;">🚖 Booking Confirmed</h2>
#           <p>Hello <strong>{booking.first_name}</strong>,</p>
#           <p>Your taxi has been booked successfully.</p>
#           <p><strong>Fare:</strong> EUR {predicted_price}</p>
#           <p><strong>Pickup:</strong> {booking.pickup_location}</p>
#           <p><strong>Dropoff:</strong> {booking.dropoff_location}</p>
#           <p>Thank you!</p>
#         </div>
#       </body>
#     </html>
#     """
#     send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message, fail_silently=False)
#
# def send_admin_emails(booking, predicted_price, promo_code):
#     from_email = settings.DEFAULT_FROM_EMAIL
#     subject = "🚨 New Booking Received"
#     html_message = f"""
#     <html>
#       <body>
#         <h2>New Booking Alert!</h2>
#         <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
#         <p><strong>Email:</strong> {booking.email}</p>
#         <p><strong>Phone:</strong> {booking.phone}</p>
#         <p><strong>Pickup:</strong> {booking.pickup_location}</p>
#         <p><strong>Dropoff:</strong> {booking.dropoff_location}</p>
#         <p><strong>Pickup Address:</strong> {booking.pickup_address}</p>
#         <p><strong>Dropoff Address:</strong> {booking.dropoff_address}</p>
#         <p><strong>Trip Type:</strong> {booking.trip_type}</p>
#         <p><strong>Transport:</strong> {booking.transport_type}</p>
#         <p><strong>Adults:</strong> {booking.adults}, <strong>Children:</strong> {booking.children}</p>
#         <p><strong>Luggage:</strong> {booking.luggage}</p>
#         <p><strong>Fare:</strong> EUR {predicted_price} (Final: EUR {booking.price})</p>
#         <p><strong>Promo:</strong> {promo_code or "No"}</p>
#         <p><strong>Time:</strong> {booking.created_at}</p>
#       </body>
#     </html>
#     """
#     email = EmailMultiAlternatives(subject, "Booking info", from_email, ['linusfit12@gmail.com'])
#     email.attach_alternative(html_message, "text/html")
#     email.send(fail_silently=False)
#
# # -------------------------------
# # Main View
# # -------------------------------
# from django.utils import timezone
# import logging
#
# logger = logging.getLogger(__name__)
#
# def predict_price_and_book(request):
#     predicted_price = None
#     booking_form = BookingForm(request.POST or None)
#
#     if request.method == "POST":
#         try:
#             # Prepare ML input features
#             features = prepare_features(request)
#             predicted_price = predict_price(features)
#
#             if booking_form.is_valid():
#                 booking = booking_form.save(commit=False)
#                 booking.price = predicted_price
#                 booking.created_at = timezone.now()
#
#                 # Handle promo code manually from promo_code_input
#                 promo_code_input = booking_form.cleaned_data.get("promo_code_input")
#                 if promo_code_input:
#                     from .models import PromoCode
#                     promo = PromoCode.objects.filter(code__iexact=promo_code_input, active=True).first()
#                     if promo and promo.valid_from <= timezone.now() <= promo.valid_until:
#                         booking.price = round(booking.price * (1 - promo.discount_percentage / 100), 2)
#                         booking.promo_code = promo
#
#                 booking.save()
#
#                 # Send confirmation emails
#                 send_user_confirmation_email(booking, predicted_price)
#                 send_admin_emails(booking, predicted_price, booking.promo_code)
#
#                 return render(request, "url/booking.html", {
#                     "booking": booking,
#                     "predicted_price": predicted_price
#                 })
#
#             else:
#                 # Print form errors to console or logs
#                 print("FORM ERRORS:", booking_form.errors)
#                 messages.error(request, "Please fix the errors in the form.")
#
#         except Exception as e:
#             logger.error(f"Error during booking: {e}", exc_info=True)
#             messages.error(request, "Something went wrong while processing your booking.")
#
#     return render(request, "url/bookingpage.html", {
#         "form": booking_form,
#         "predicted_price": predicted_price,
#         "google_api_key": settings.GOOGLE_MAPS_API_KEY,
#     })