import numpy as np
from django.shortcuts import render, get_object_or_404
import logging
from django.conf import settings
from django.contrib import messages
# Create your views here.
from book.views import _price_for_legs, send_user_confirmation_email, send_admin_emails, logger
from booking.views import load_model, get_float_value
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

def index(request):
    """
    Homepage: renders hero/sections + booking form.
    On POST, processes a booking (same as booking_view) and shows success page.
    """
    canonical_url = request.build_absolute_uri()

    # SEO + sections
    try:
        seo_settings = SEOSettings.objects.get(title='Home')
    except SEOSettings.DoesNotExist:
        seo_settings = None

    slider_items = Slider.objects.filter(is_active=True).order_by('order')
    about = About.objects.first()
    cabs = Cab.objects.prefetch_related('amenities').all()
    amenity = Amenity.objects.all()
    services = Service.objects.all()
    faqs = FAQ.objects.all()
    blogs = Blog.objects.order_by('-date')

    # Booking form on homepage
    form = BookingForm(request.POST or None)

    if request.method == "POST":
        try:
            if form.is_valid():
                cd = form.cleaned_data
                # Leg 1
                p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
                pa1, da1 = cd.get("pickup_address_1", ""), cd.get("dropoff_address_1", "")
                # Leg 2 (optional)
                p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
                pa2, da2 = cd.get("pickup_address_2", ""), cd.get("dropoff_address_2", "")

                # If round trip and leg2 omitted, auto reverse (addresses reversed too)
                if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
                    p2, d2 = d1, p1
                    pa2, da2 = da1, pa1

                pax = _pax(cd.get("passengers") or 1)

                legs = [{"p": p1.id, "d": d1.id}]
                if cd.get("trip_type") == "Round Trip":
                    legs.append({"p": p2.id, "d": d2.id})

                price = _price_for_legs(
                    trip_type=cd.get("trip_type"),
                    transport_type=cd.get("transport_type"),
                    legs=legs,
                    pickup_time=cd.get("pickup_time"),
                    return_time=cd.get("return_time"),
                    pax=pax
                )

                booking = form.save(commit=False)
                booking.created_at = timezone.now()
                booking.pickup_location = p1
                booking.dropoff_location = d1
                booking.pickup_address = pa1
                booking.dropoff_address = da1
                booking.price = price
                booking.save()
                if hasattr(form, "save_m2m"):
                    form.save_m2m()

                # Save legs
                TripLeg.objects.create(
                    booking=booking, sequence=1,
                    pickup_location=p1, dropoff_location=d1,
                    pickup_address=pa1, dropoff_address=da1
                )
                if cd.get("trip_type") == "Round Trip":
                    TripLeg.objects.create(
                        booking=booking, sequence=2,
                        pickup_location=p2, dropoff_location=d2,
                        pickup_address=pa2, dropoff_address=da2
                    )

                # Recalculate for safety (promo/night, etc.)
                booking.calculate_total_price(passengers_override=pax)

                # Emails
                send_user_confirmation_email(booking)
                send_admin_emails(booking)

                return render(request, "booking/booking_success.html", {"booking": booking})
            else:
                messages.error(request, "Please fix the errors in the form.")
                logger.warning(f"Form errors on index: {form.errors}")
        except Exception as e:
            logger.error(f"Error during booking on index: {e}", exc_info=True)
            messages.error(request, "Something went wrong while processing your booking.")

    context = {
        "canonical_url": canonical_url,
        "seo_settings": seo_settings,
        "slider_items": slider_items,
        "about": about,
        "cabs": cabs,
        "amenity": amenity,
        "services": services,
        "faqs": faqs,
        "blogs": blogs,
        "form": form,
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    }
    return render(request, "core/index.html", context)


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