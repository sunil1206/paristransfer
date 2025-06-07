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


# def predict_price_and_book(request):
#     predicted_price = None
#     booking = None  # Variable to store booking instance
#     if request.method == "POST":
#         try:
#             # Extract features from the form
#             features = np.array([[
#                 get_float_value(request, "trip_type"),
#                 get_float_value(request, "pickup_location"),
#                 get_float_value(request, "dropoff_location"),
#                 get_float_value(request, "transport_type"),
#                 get_float_value(request, "adults"),
#                 get_float_value(request, "children"),
#                 # get_float_value(request, "luggage"),
#                 get_float_value(request, "pickup_time"),
#                 get_float_value(request, "return_time"),
#             ]])
#             # Load the trained model
#             # price_model = load_model('booking/models/taxi_price_classifier.joblib')
#             price_model = load_model('booking/models/taxi_price_classifier.joblib')
#             # Predict the price using the model
#             predicted_price = round(price_model.predict(features)[0], 2)
#             # Handle booking creation
#             booking_form = BookingForm(request.POST)
#             if booking_form.is_valid():
#                 # Create booking instance
#                 booking = booking_form.save(commit=False)
#                 booking.price = predicted_price  # Set the predicted price
#                 booking.created_at = timezone.now()
#                 # Optional: Handle promo code application
#                 promo_code = booking_form.cleaned_data.get('promo_code')
#                 if promo_code:
#                     try:
#                         promo = PromoCode.objects.get(code=promo_code)
#                         if promo.valid_from <= timezone.now() <= promo.valid_until and promo.active:
#                             discount = (promo.discount_percentage / 100) * booking.price
#                             booking.price -= discount  # Apply discount to price
#                     except PromoCode.DoesNotExist:
#                         booking.promo_code = None  # No valid promo code
#                 # Save booking to the database
#                 booking.save()
#                 # Send confirmation email with HTML formatting
#                 subject = "🎉 Booking Confirmation – Your Ride is Booked!"
#                 plain_message = f"Dear {booking.first_name},\n\nYour booking is confirmed. The predicted price is ${predicted_price}."
#                 from_email = settings.DEFAULT_FROM_EMAIL
#                 recipient_list = [booking.email,'linusfit12@gmail.com']
#                 html_message = f"""
#                                 <html>
#                                   <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
#                                     <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0px 2px 10px rgba(0,0,0,0.1); margin: auto;">
#                                       <h2 style="color: #4CAF50;">🚖 Your Booking is Confirmed!</h2>
#                                       <p>Hi <strong>{booking.first_name}</strong>,</p>
#                                       <p>Thank you for choosing our taxi service. We're excited to take you where you need to go!</p>
#                                       <p><strong>Predicted Fare:</strong> <span style="color: #2196F3;">    EUR {predicted_price}</span></p>
#                                       <p>We’ll be in touch if there are any updates. Until then, sit back and relax—we’ve got your ride covered!</p>
#                                       <br>
#                                       <p style="margin-top: 40px;">Warm regards,<br><strong>Your Taxi Service Team</strong></p>
#                                     </div>
#                                   </body>
#                                 </html>
#                                 """
#
#                 send_mail(
#                     subject,
#                     plain_message,
#                     from_email,
#                     recipient_list,
#                     html_message=html_message,
#                 )
#
#                 return render(request, 'booking/booking.html', {'booking': booking, 'predicted_price': predicted_price})
#         except Exception as e:
#             print(f"Error occurred: {e}")  # Debugging
#             predicted_price = f"Error: {e}"
#     else:
#         booking_form = BookingForm()
#     return render(request, 'url/bookingpage.html', {'form': booking_form, 'predicted_price': predicted_price})

from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from booking.forms import BookingForm
from booking.models import PromoCode
# from booking.utils import get_float_value, load_model  # Your helper functions
import numpy as np
import joblib
import numpy as np
import pandas as pd
#
#
# def predict_price_and_book(request):
#     predicted_price = None
#     booking = None  # Variable to store booking instance
#     booking_form = BookingForm(request.POST) if request.method == "POST" else BookingForm()
#
#     if request.method == "POST":
#         try:
#             # Extract features from the form and convert to pandas DataFrame
#             features_dict = {
#                 "trip_type": get_float_value(request, "trip_type"),
#                 "pickup_location": get_float_value(request, "pickup_location"),
#                 "dropoff_location": get_float_value(request, "dropoff_location"),
#                 "transport_type": get_float_value(request, "transport_type"),
#                 "adults": get_float_value(request, "adults"),
#                 "children": get_float_value(request, "children"),
#                 "pickup_time": get_float_value(request, "pickup_time"),
#                 "return_time": get_float_value(request, "return_time"),
#             }
#
#             # Convert the dictionary to a pandas DataFrame for prediction
#             features_df = pd.DataFrame([features_dict])
#
#             # Load the trained model
#             price_model = load_model('booking/models/price_model.joblib')
#
#             # Predict the price using the model
#             predicted_price = round(price_model.predict(features_df)[0], 2)
#
#             # Handle booking creation
#             if booking_form.is_valid():
#                 booking = booking_form.save(commit=False)
#                 booking.price = predicted_price
#                 booking.created_at = timezone.now()
#
#                 # Optional: Handle promo code application
#                 promo_code = booking_form.cleaned_data.get('promo_code')
#                 if promo_code:
#                     try:
#                         promo = PromoCode.objects.get(code=promo_code)
#                         if promo.valid_from <= timezone.now() <= promo.valid_until and promo.active:
#                             discount = (promo.discount_percentage / 100) * booking.price
#                             booking.price -= discount
#                     except PromoCode.DoesNotExist:
#                         booking.promo_code = None
#
#                 # Save booking to the database
#                 booking.save()
#
#                 # Send confirmation email with HTML formatting
#                 subject = " Booking Confirmation – Your Ride is Booked!"
#                 plain_message = f"Dear {booking.first_name},\n\nYour booking is confirmed. The predicted price is EUR {predicted_price}."
#                 from_email = settings.DEFAULT_FROM_EMAIL
#                 recipient_list = [booking.email, 'linusfit12@gmail.com']
#                 html_message = f"""
#                                 <html>
#                                   <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
#                                     <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0px 2px 10px rgba(0,0,0,0.1); margin: auto;">
#                                       <h2 style="color: #4CAF50;">🚖 Your Booking is Confirmed!</h2>
#                                       <p>Hi <strong>{booking.first_name}</strong>,</p>
#                                       <p>Thank you for choosing our taxi service. We're excited to take you where you need to go!</p>
#                                       <p><strong>Predicted Fare:</strong> <span style="color: #2196F3;">EUR {predicted_price}</span></p>
#                                       <p>We’ll be in touch if there are any updates. Until then, sit back and relax—we’ve got your ride covered!</p>
#                                       <br>
#                                       <p style="margin-top: 40px;">Warm regards,<br><strong>Your Taxi Service Team</strong></p>
#                                     </div>
#                                   </body>
#                                 </html>
#                                 """
#
#                 send_mail(
#                     subject,
#                     plain_message,
#                     from_email,
#                     recipient_list,
#                     html_message=html_message,
#                 )
#
#                 # Render the confirmation page with the booking and predicted price
#                 return render(request, 'booking/booking.html', {'booking': booking, 'predicted_price': predicted_price})
#
#         except Exception as e:
#             print(f"Error occurred: {e}")  # Debugging
#             predicted_price = f"Error: {e}"
#
#     return render(request, 'url/bookingpage.html', {'form': booking_form, 'predicted_price': predicted_price})


from django.shortcuts import render
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib import messages
import pandas as pd
import os
import joblib

# === Mapping Dictionaries ===
TRIP_TYPE_MAPPING = {
    "0": "OneWay",
    "1": "Round Trip",
}

PICKUP_LOCATION_MAPPING = {
    "0": "BEAUVAIS",
    "1": "Bayeux",
    "2": "CDG(Charles de Gaulle Airport)",
    "3": "Fontainebleau",
    "4": "ORLY (Orly Airport)",
    "5": "Paris hotels / Train Stations",
    "6": "Reims",
}

DROPOFF_LOCATION_MAPPING = {
    "0": "BEAUVAIS",
    "1": "CDG",
    "2": "Disneyland",
    "3": "ORLY (Orly Airport)",
    "4": "Paris hotels / Train Stations",
}

TRANSPORT_TYPE_MAPPING = {
    "0": "Car",
    "1": "Van",
}

PICKUP_TIME_MAPPING = {
    "0": "After 10",
    "1": "Before 10",
}

RETURN_TIME_MAPPING = {
    "0": "After 10",
    "1": "Before 10",
}


def load_model(path):
    return joblib.load(path)


# def predict_price_and_book(request):
#     predicted_price = None
#     booking = None
#     booking_form = BookingForm(request.POST) if request.method == "POST" else BookingForm()
#
#     if request.method == "POST":
#         try:
#             # Extract features from the form
#             features_dict = {
#                 "trip_type": get_float_value(request, "trip_type"),
#                 "pickup_location": get_float_value(request, "pickup_location"),
#                 "dropoff_location": get_float_value(request, "dropoff_location"),
#                 "transport_type": get_float_value(request, "transport_type"),
#                 "adults": get_float_value(request, "adults"),
#                 "children": get_float_value(request, "children"),
#                 "pickup_time": get_float_value(request, "pickup_time"),
#                 "return_time": get_float_value(request, "return_time"),
#             }
#             features_df = pd.DataFrame([features_dict])
#
#             # Load the model
#             model_path = os.path.join(settings.BASE_DIR, 'booking/models/price_model.joblib')
#
#             price_model = load_model(model_path)
#
#             # Predict
#             predicted_price = round(price_model.predict(features_df)[0], 2)
#
#             if booking_form.is_valid():
#                 booking = booking_form.save(commit=False)
#                 booking.price = predicted_price
#                 booking.created_at = timezone.now()
#
#                 # Promo code logic
#                 promo_code = booking_form.cleaned_data.get('promo_code')
#                 if promo_code:
#                     try:
#                         promo = PromoCode.objects.get(code=promo_code)
#                         if promo.valid_from <= timezone.now() <= promo.valid_until and promo.active:
#                             discount = (promo.discount_percentage / 100) * booking.price
#                             booking.price -= discount
#                     except PromoCode.DoesNotExist:
#                         booking.promo_code = None
#
#                 booking.save()
#
#                 # --- Main confirmation email (user + admin) ---
#                 subject = "Booking Confirmation – Your Ride is Booked!"
#                 plain_message = f"Dear {booking.first_name},\n\nYour booking is confirmed. The predicted price is EUR {predicted_price}."
#                 from_email = settings.DEFAULT_FROM_EMAIL
#                 recipient_list = [booking.email]
#                 html_message = f"""
#                     <html>
#                                   <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
#                                     <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0px 2px 10px rgba(0,0,0,0.1); margin: auto;">
#                                       <h2 style="color: #4CAF50;">🚖 Your Booking is Confirmed!</h2>
#                                       <p>Hi <strong>{booking.first_name}</strong>,</p>
#                                       <p>Thank you for choosing our taxi service. We're excited to take you where you need to go!</p>
#                                       <p><strong>Predicted Fare:</strong> <span style="color: #2196F3;">EUR {predicted_price}</span></p>
#                                       <p>We’ll be in touch if there are any updates. Until then, sit back and relax—we’ve got your ride covered!</p>
#                                       <br>
#                                       <p style="margin-top: 40px;">Warm regards,<br><strong>Your Taxi Service Team</strong></p>
#                                     </div>
#                                   </body>
#                                 </html>
#                 """
#                 send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
#
#                 # --- Admin-only detailed notification ---
#                 admin_subject = "🚨 New Booking Received"
#                 admin_html = f"""
#                     <html>
#                       <body>
#                         <h2>New Booking Alert!</h2>
#                         <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
#                         <p><strong>Email:</strong> {booking.email}</p>
#                         <p><strong>Pickup:</strong> {booking.pickup_location}</p>
#                         <p><strong>Dropoff:</strong> {booking.dropoff_location}</p>
#                         <p><strong>Fare:</strong> EUR {predicted_price}</p>
#                         <p><strong>Booking Time:</strong> {booking.created_at}</p>
#                       </body>
#                     </html>
#                 """
#                 email = EmailMultiAlternatives(admin_subject, "New booking received.", from_email,
#                                                ['linusfit12@gmail.com'])
#                 email.attach_alternative(admin_html, "text/html")
#                 email.send()
#
#                 # --- Admin-only summary email ---
#                 summary_subject = "📊 Booking Summary Report"
#                 summary_html = f"""
#                     <html>
#                       <body>
#                         <h3>Booking Summary</h3>
#                         <ul>
#                           <li>Trip Type: {booking.trip_type}</li>
#                           <li>Transport Type: {booking.transport_type}</li>
#                           <li>Adults: {booking.adults}</li>
#                           <li>Children: {booking.children}</li>
#                           <li>Promo Applied: {promo_code or 'No'}</li>
#                         </ul>
#                       </body>
#                     </html>
#                 """
#                 summary_email = EmailMultiAlternatives(summary_subject, "Booking summary report.", from_email,
#                                                        ['linusfit12@gmail.com'])
#                 summary_email.attach_alternative(summary_html, "text/html")
#                 summary_email.send()
#
#                 return render(request, 'booking/booking.html', {'booking': booking, 'predicted_price': predicted_price})
#
#         except Exception as e:
#             print(f"Error: {e}")
#             messages.error(request, "An error occurred while processing your booking.")
#
#     return render(request, 'url/bookingpage.html', {'form': booking_form, 'predicted_price': predicted_price})
#



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
# Reverse Mapping for decoding
# -------------------------------
REVERSE_LOCATION_MAP = {
    0: "BEAUVAIS",
    1: "Bayeux",
    2: "CDG(Charles de Gaulle Airport)",
    3: "Fontainebleau",
    4: "ORLY (Orly Airport)",
    5: "Paris hotels / Train Stations",
    6: "Reims",
    7: "Disneyland",
}

REVERSE_TRIP_TYPE = {
    0: "One Way",
    1: "Round Trip"
}

REVERSE_TRANSPORT_TYPE = {
    0: "Car",
    1: "Van"
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
        "trip_type": get_float_value(request, "trip_type"),
        "pickup_location": get_float_value(request, "pickup_location"),
        "dropoff_location": get_float_value(request, "dropoff_location"),
        "transport_type": get_float_value(request, "transport_type"),
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

def send_user_confirmation_email(booking, predicted_price):
    subject = "Booking Confirmation – Your Ride is Booked!"
    plain_message = f"Dear {booking.first_name},\n\nYour booking is confirmed. The predicted price is EUR {predicted_price}."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [booking.email]
    html_message = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0px 2px 10px rgba(0,0,0,0.1); margin: auto;">
              <h2 style="color: #4CAF50;">🚖 Your Booking is Confirmed!</h2>
              <p>Hi <strong>{booking.first_name}</strong>,</p>
              <p>Thank you for choosing our taxi service. We're excited to take you where you need to go!</p>
              <p><strong>Predicted Fare:</strong> <span style="color: #2196F3;">EUR {predicted_price}</span></p>
              <p>We’ll be in touch if there are any updates. Until then, sit back and relax—we’ve got your ride covered!</p>
              <br>
              <p style="margin-top: 40px;">Warm regards,<br><strong>Your Taxi Service Team</strong></p>
            </div>
          </body>
        </html>
    """
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_admin_emails(booking, predicted_price, promo_code):
    from_email = settings.DEFAULT_FROM_EMAIL

    pickup_readable = REVERSE_LOCATION_MAP.get(int(booking.pickup_location), 'Unknown')
    dropoff_readable = REVERSE_LOCATION_MAP.get(int(booking.dropoff_location), 'Unknown')
    trip_type_readable = REVERSE_TRIP_TYPE.get(int(booking.trip_type), 'Unknown')
    transport_type_readable = REVERSE_TRANSPORT_TYPE.get(int(booking.transport_type), 'Unknown')

    # Detailed notification
    admin_subject = "🚨 New Booking Received"
    admin_html = f"""
        <html>
          <body>
            <h2>New Booking Alert!</h2>
            <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
            <p><strong>Email:</strong> {booking.email}</p>
            <p><strong>Pickup:</strong> {pickup_readable}</p>
            <p><strong>Dropoff:</strong> {dropoff_readable}</p>
            <p><strong>Fare:</strong> EUR {predicted_price}</p>
            <p><strong>Booking Time:</strong> {booking.created_at}</p>
          </body>
        </html>
    """
    email = EmailMultiAlternatives(admin_subject, "New booking received.", from_email, ['linusfit12@gmail.com'])
    email.attach_alternative(admin_html, "text/html")
    email.send()

    # Summary email
    summary_subject = "📊 Booking Summary Report"
    summary_html = f"""
        <html>
          <body>
            <h3>Booking Summary</h3>
            <ul>
              <li>Trip Type: {trip_type_readable}</li>
              <li>Transport Type: {transport_type_readable}</li>
              <li>Adults: {booking.adults}</li>
              <li>Children: {booking.children}</li>
              <li>Promo Applied: {promo_code or 'No'}</li>
              <li>Final Fare: EUR {booking.price}</li>
            </ul>
          </body>
        </html>
    """
    summary_email = EmailMultiAlternatives(summary_subject, "Booking summary report.", from_email, ['linusfit12@gmail.com'])
    summary_email.attach_alternative(summary_html, "text/html")
    summary_email.send()

# -------------------------------
# Main View
# -------------------------------

def predict_price_and_book(request):
    predicted_price = None
    booking = None
    booking_form = BookingForm(request.POST) if request.method == "POST" else BookingForm()

    if request.method == "POST":
        try:
            features = prepare_features(request)
            predicted_price = predict_price(features)

            if booking_form.is_valid():
                booking = booking_form.save(commit=False)
                booking.price = predicted_price
                booking.created_at = timezone.now()

                promo_code = booking_form.cleaned_data.get('promo_code')
                if promo_code:
                    booking.price = apply_promo_code(promo_code, booking.price)
                    booking.promo_code = promo_code

                booking.save()

                send_user_confirmation_email(booking, predicted_price)
                send_admin_emails(booking, predicted_price, promo_code)

                return render(request, 'booking/booking.html', {'booking': booking, 'predicted_price': predicted_price})
            else:
                messages.error(request, "Please correct the errors in the form.")

        except Exception as e:
            logger.error(f"Booking processing failed: {e}", exc_info=True)
            messages.error(request, "An error occurred while processing your booking. Please try again.")

    return render(request, 'url/bookingpage.html', {'form': booking_form, 'predicted_price': predicted_price})
