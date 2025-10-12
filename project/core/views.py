import numpy as np
from django.shortcuts import render, get_object_or_404
import logging
from django.conf import settings
from django.contrib import messages
# Create your views here.
from book.views import logger
from book.notifications import send_sms_notifications, send_admin_emails, send_user_confirmation_email
from core.models import Slider, About, Cab, Amenity, Service, FAQ, Blog
from seo.models import SEOSettings
from django.utils import timezone
def handling_404(request, exception):
    return render(request, 'core/404.html', {})

# app/views.py (add below your imports and helpers)

from book.forms import BookingForm
from book.models import (
    TripLeg, PricingRule, find_matrix_price,
)

# app/views.py
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from book.forms import BookingForm
from book.models import TripLeg
from book.views import logger

from core.models import Slider, About, Cab, Amenity, Service, FAQ, Blog
from seo.models import SEOSettings

# app/views.py (inside same file as booking_view)
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Count

# Import notification functions from your booking app
# (Or move them into a separate 'utils.py' file for better organization)
# Import models and forms
from .models import Slider, About, Cab, Amenity, Service, FAQ, Blog
from book.forms import BookingForm
from book.models import Location, TripLeg

logger = logging.getLogger(__name__)


def index(request):
    """
    Handles both displaying the homepage (GET) and processing
    a new booking submission (POST).
    """
    # Instantiate the form, binding it to POST data if available
    form = BookingForm(request.POST or None)

    # --- HANDLE FORM SUBMISSION (POST Request) ---
    if request.method == "POST":
        if form.is_valid():
            try:
                # This logic is copied directly from your original booking_view
                cd = form.cleaned_data

                # Default logic for Round Trip return locations
                p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
                p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
                if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
                    p2, d2 = d1, p1

                # Save the booking and create TripLegs
                booking = form.save()

                TripLeg.objects.create(
                    booking=booking,
                    sequence=1,
                    pickup_location=p1,
                    dropoff_location=d1,
                    pickup_address=cd.get("pickup_address_1", ""),
                    dropoff_address=cd.get("dropoff_address_1", "")
                )
                if cd.get("trip_type") == "Round Trip":
                    TripLeg.objects.create(
                        booking=booking,
                        sequence=2,
                        pickup_location=p2,
                        dropoff_location=d2,
                        pickup_address=cd.get("pickup_address_2", ""),
                        dropoff_address=cd.get("dropoff_address_2", "")
                    )

                # Calculate final price and send notifications
                total_passengers = cd.get("adults", 1) + cd.get("children", 0)
                booking.calculate_total_price(passengers_override=total_passengers)

                send_user_confirmation_email(booking)
                send_admin_emails(booking)
                send_sms_notifications(booking)

                # Redirect to a success page upon successful booking
                return render(request, "booking/booking_success.html", {"booking": booking})

            except Exception as e:
                logger.error(f"Error during booking submission from index page: {e}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            # If form is invalid, log errors and add a message
            logger.warning(f"Index page booking form errors: {form.errors.as_json()}")
            messages.error(request, "Please correct the errors below and try again.")

    # --- DISPLAY HOMEPAGE (GET Request or Invalid POST) ---
    # This part runs for initial page loads and when the POST form is invalid,
    # ensuring the page re-renders correctly with all necessary context.

    main_locations = Location.objects.filter(is_main_location=True).annotate(
        sub_location_count=Count('sub_locations')
    ).order_by('name')

    context = {
        # The form is passed here (either empty or with errors)
        "form": form,
        "main_locations": main_locations,
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),

        # All the homepage content
        "slider_items": Slider.objects.filter(is_active=True).order_by("order"),
        "about": About.objects.first(),
        "cabs": Cab.objects.prefetch_related("amenities").all(),
        "amenities": Amenity.objects.all(),
        "services": Service.objects.all(),
        "faqs": FAQ.objects.all(),
        "blogs": Blog.objects.order_by("-date")[:3],
    }

    return render(request, "core/index.html", context)
# def index(request):
#     canonical_url = request.build_absolute_uri()
#
#     # SEO + homepage sections
#     try:
#         seo_settings = SEOSettings.objects.get(title="Home")
#     except SEOSettings.DoesNotExist:
#         seo_settings = None
#
#     slider_items = Slider.objects.filter(is_active=True).order_by("order")
#     about = About.objects.first()
#     cabs = Cab.objects.prefetch_related("amenities").all()
#     amenity = Amenity.objects.all()
#     services = Service.objects.all()
#     faqs = FAQ.objects.all()
#     blogs = Blog.objects.order_by("-date")
#
#     # Booking form
#     form = BookingForm(request.POST or None)
#
#     if request.method == "POST":
#         if form.is_valid():
#             try:
#                 cd = form.cleaned_data
#
#                 # --- Leg 1 ---
#                 p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
#                 pa1 = cd.get("pickup_address_1") or cd.get("pickup_address") or ""
#                 da1 = cd.get("dropoff_address_1") or cd.get("dropoff_address") or ""
#
#                 # --- Leg 2 (optional) ---
#                 p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
#                 pa2 = cd.get("pickup_address_2") or ""
#                 da2 = cd.get("dropoff_address_2") or ""
#
#                 # Auto-reverse if round trip & no return leg given
#                 if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
#                     p2, d2 = d1, p1
#                     pa2, da2 = da1, pa1
#
#                 pax = _pax(cd.get("passengers") or 1)
#
#                 # Legs for price calculation
#                 legs = [{"p": p1.id, "d": d1.id}]
#                 if cd.get("trip_type") == "Round Trip":
#                     legs.append({"p": p2.id, "d": d2.id})
#
#                 price = _price_for_legs(
#                     trip_type=cd.get("trip_type"),
#                     transport_type=cd.get("transport_type"),
#                     legs=legs,
#                     pickup_time=cd.get("pickup_time"),
#                     return_time=cd.get("return_time"),
#                     pax=pax,
#                 )
#
#                 # Save booking summary
#                 booking = form.save(commit=False)
#                 booking.created_at = timezone.now()
#                 booking.pickup_location = p1
#                 booking.dropoff_location = d1
#                 booking.pickup_address = pa1
#                 booking.dropoff_address = da1
#                 booking.price = price
#                 booking.save()
#                 if hasattr(form, "save_m2m"):
#                     form.save_m2m()
#
#                 # Save legs
#                 TripLeg.objects.create(
#                     booking=booking, sequence=1,
#                     pickup_location=p1, dropoff_location=d1,
#                     pickup_address=pa1, dropoff_address=da1,
#                 )
#                 if cd.get("trip_type") == "Round Trip":
#                     TripLeg.objects.create(
#                         booking=booking, sequence=2,
#                         pickup_location=p2, dropoff_location=d2,
#                         pickup_address=pa2, dropoff_address=da2,
#                     )
#
#                 # Recalculate safely (applies promo/night logic again)
#                 booking.calculate_total_price(passengers_override=pax)
#
#                 # Emails
#                 send_user_confirmation_email(booking)
#                 send_admin_emails(booking)
#
#                 messages.success(request, "Your booking has been confirmed!")
#                 return render(request, "core/index.html", {
#                     **{
#                         "canonical_url": canonical_url,
#                         "seo_settings": seo_settings,
#                         "slider_items": slider_items,
#                         "about": about,
#                         "cabs": cabs,
#                         "amenity": amenity,
#                         "services": services,
#                         "faqs": faqs,
#                         "blogs": blogs,
#                         "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
#                     },
#                     "form": BookingForm(),  # reset form
#                     "booking": booking,
#                 })
#
#             except Exception as e:
#                 logger.error(f"Error during booking on index: {e}", exc_info=True)
#                 messages.error(request, "Something went wrong while processing your booking.")
#         else:
#             messages.error(request, "Please fix the errors in the form.")
#             logger.warning(f"Form errors on index: {form.errors}")
#
#     context = {
#         "canonical_url": canonical_url,
#         "seo_settings": seo_settings,
#         "slider_items": slider_items,
#         "about": about,
#         "cabs": cabs,
#         "amenity": amenity,
#         "services": services,
#         "faqs": faqs,
#         "blogs": blogs,
#         "form": form,
#         "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
#     }
#     return render(request, "core/index.html", context)

# def index(request):
#     canonical_url = request.build_absolute_uri()
#
#     # SEO + sections
#     try:
#         seo_settings = SEOSettings.objects.get(title='Home')
#     except SEOSettings.DoesNotExist:
#         seo_settings = None
#
#     slider_items = Slider.objects.filter(is_active=True).order_by('order')
#     about = About.objects.first()
#     cabs = Cab.objects.prefetch_related('amenities').all()
#     amenity = Amenity.objects.all()
#     services = Service.objects.all()
#     faqs = FAQ.objects.all()
#     blogs = Blog.objects.order_by('-date')
#
#     # Booking form on homepage
#     form = BookingForm(request.POST or None)
#
#     if request.method == "POST":
#         if form.is_valid():
#             try:
#                 cd = form.cleaned_data
#
#                 # Leg 1
#                 p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
#                 pa1, da1 = cd.get("pickup_address_1", ""), cd.get("dropoff_address_1", "")
#
#                 # Leg 2 (optional / round trip)
#                 p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
#                 pa2, da2 = cd.get("pickup_address_2", ""), cd.get("dropoff_address_2", "")
#
#                 if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
#                     p2, d2 = d1, p1
#                     pa2, da2 = da1, pa1
#
#                 pax = cd.get("passengers") or 1
#
#                 # Price calculation
#                 legs = [{"p": p1.id, "d": d1.id}]
#                 if cd.get("trip_type") == "Round Trip":
#                     legs.append({"p": p2.id, "d": d2.id})
#
#                 price = _price_for_legs(
#                     trip_type=cd.get("trip_type"),
#                     transport_type=cd.get("transport_type"),
#                     legs=legs,
#                     pickup_time=cd.get("pickup_time"),
#                     return_time=cd.get("return_time"),
#                     pax=pax
#                 )
#
#                 # Save booking
#                 booking = form.save(commit=False)
#                 booking.created_at = timezone.now()
#                 booking.pickup_location = p1
#                 booking.dropoff_location = d1
#                 booking.pickup_address = pa1
#                 booking.dropoff_address = da1
#                 booking.price = price
#                 booking.save()
#                 if hasattr(form, "save_m2m"):
#                     form.save_m2m()
#
#                 # Save trip legs
#                 TripLeg.objects.create(
#                     booking=booking, sequence=1,
#                     pickup_location=p1, dropoff_location=d1,
#                     pickup_address=pa1, dropoff_address=da1
#                 )
#                 if cd.get("trip_type") == "Round Trip":
#                     TripLeg.objects.create(
#                         booking=booking, sequence=2,
#                         pickup_location=p2, dropoff_location=d2,
#                         pickup_address=pa2, dropoff_address=da2
#                     )
#
#                 # Recalculate total price (promo/night logic)
#                 booking.calculate_total_price(passengers_override=pax)
#
#                 # Send emails
#                 send_user_confirmation_email(booking)
#                 send_admin_emails(booking)
#
#                 return render(request, "core/index.html", {"booking": booking})
#
#             except Exception as e:
#                 logger.error(f"Error during booking on index: {e}", exc_info=True)
#                 messages.error(request, "Something went wrong while processing your booking.")
#         else:
#             messages.error(request, "Please fix the errors in the form.")
#             logger.warning(f"Form errors on index: {form.errors}")
#
#     context = {
#         "canonical_url": canonical_url,
#         "seo_settings": seo_settings,
#         "slider_items": slider_items,
#         "about": about,
#         "cabs": cabs,
#         "amenity": amenity,
#         "services": services,
#         "faqs": faqs,
#         "blogs": blogs,
#         "form": form,
#         "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
#     }
#     return render(request, "core/index.html", context)



# def index(request):
#     canonical_url = request.build_absolute_uri()
#     try:
#         seo_settings = SEOSettings.objects.get(title='Home')
#     except SEOSettings.DoesNotExist:
#         seo_settings = None  # Or provide default SEO settings
#
#     slider_items = Slider.objects.filter(is_active=True).order_by('order')
#     about = About.objects.first()
#     cabs = Cab.objects.prefetch_related('amenities').all()
#     amenity = Amenity.objects.all()
#     services = Service.objects.all()
#     faqs = FAQ.objects.all()
#     # blog_posts = Blog.objects.all()
#     blogs = Blog.objects.order_by('-date')  # Newest first
#
#     # Prediction logic
#     predicted_price = None
#     if request.method == "POST":
#         try:
#             print("Received POST request with data:", request.POST)  # Debugging
#
#             # Extract features from the form
#             features = np.array([[
#                 get_float_value(request, "trip_type"),
#                 get_float_value(request, "pickup_location"),
#                 get_float_value(request, "dropoff_location"),
#                 get_float_value(request, "transport_type"),
#                 get_float_value(request, "adults"),
#                 get_float_value(request, "children"),
#                 get_float_value(request, "luggage"),
#                 get_float_value(request, "pickup_time"),
#                 get_float_value(request, "return_time"),
#             ]])
#
#             # Load the trained model
#             price_model = load_model('booking/models/taxi_price_classifier.joblib')
#
#             print("Predicting with features:", features)  # Debugging
#             predicted_price = round(price_model.predict(features)[0])
#
#         except Exception as e:
#             print(f"Error occurred: {e}")  # Debugging
#             predicted_price = f"Error: {e}"
#
#     context = {
#         'canonical_url': canonical_url,
#         'seo_settings': seo_settings,
#         'slider_items': slider_items,
#         'about': about,
#         'cabs': cabs,
#         'amenity': amenity,
#         'services': services,
#         'faqs': faqs,
#         # 'blog_posts': blog_posts,
#         'predicted_price': predicted_price,  # Add predicted price to context
#         'blogs':blogs,
#     }
#     return render(request, 'core/index.html', context)



def about(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='About Us')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings
    about = About.objects.first()
    faqs = FAQ.objects.all()
    context = {'canonical_url': canonical_url,
               'seo_settings': seo_settings,
               'about':about,
               'faqs':faqs
               }
    return render(request, 'url/aboutpage.html',context)

def service(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='Service')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings
    context = {'canonical_url': canonical_url,
               'seo_settings': seo_settings
               }
    return render(request, 'url/servicepage.html', context)

# def contact(request):
#     canonical_url = request.build_absolute_uri()
#     try:
#         seo_settings = SEOSettings.objects.get(title='Contact')
#     except SEOSettings.DoesNotExist:
#         seo_settings = None  # Or provide default SEO settings
#     context = {'canonical_url': canonical_url,
#                'seo_settings': seo_settings
#                }
#     return render(request, 'core/contactpage.html', context)


def blog_post(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    return render(request, 'blog/blogdetail.html', {'blog': blog})