# app/views.py
import logging
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import BookingForm
from .models import TripLeg, PricingRule, find_matrix_price

logger = logging.getLogger(__name__)

def _pax(val, default=1):
    try: return max(1, min(8, int(val)))
    except Exception: return default

def _night_charge_for(flag: str) -> float:
    rule = PricingRule.objects.filter(active=True).first()
    if not rule: return 0.0
    return float(rule.night_charge) if str(flag) == "0" else 0.0

def _price_for_legs(trip_type, transport_type, legs, pickup_time, return_time, pax):
    total = 0.0
    if trip_type == "Round Trip" and len(legs) == 2:
        l1, l2 = legs
        reverse = (l1["p"] == l2["d"] and l1["d"] == l2["p"])
        if reverse:
            total += find_matrix_price("Round Trip", transport_type, l1["p"], l1["d"], pax)
        else:
            total += find_matrix_price("One Way", transport_type, l1["p"], l1["d"], pax)
            total += find_matrix_price("One Way", transport_type, l2["p"], l2["d"], pax)
    else:
        for leg in legs:
            total += find_matrix_price("One Way", transport_type, leg["p"], leg["d"], pax)

    # night charges
    total += _night_charge_for(pickup_time)
    if trip_type == "Round Trip":
        total += _night_charge_for(return_time)
    return round(total, 2)

def send_user_confirmation_email(booking):
    subject = "Booking Confirmation – Your Ride is Booked!"
    plain = f"Dear {booking.first_name}, your booking is confirmed. Fare: EUR {booking.price}."
    html = f"""
    <html><body style="font-family: Arial; background:#f4f4f4; padding:20px;">
      <div style="max-width:600px;background:#fff;padding:30px;border-radius:10px;">
        <h2 style="color:#4CAF50;">🚖 Booking Confirmed</h2>
        <p>Hello <strong>{booking.first_name}</strong>,</p>
        <p><strong>Fare:</strong> EUR {booking.price}</p>
        <p><strong>Trip Type:</strong> {booking.trip_type}</p>
        <p><strong>Transport:</strong> {booking.transport_type}</p>
        <p><strong>Pickup Address:</strong> EUR {booking.pickup_address}</p>
        <p><strong>Dropoff Address:</strong> {booking.dropoff_address}</p>
        <p><strong>Email:</strong> {booking.email}</p>
        <p><strong>Flight Number:</strong> EUR {booking.flight_number}</p>
        <p><strong>Check-in date:</strong> {booking.checkin_date}</p>
      </div>
    </body></html>
    """
    send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, [booking.email], html_message=html, fail_silently=False)

def send_admin_emails(booking):
    html = f"""
    <html><body>
      <h2>New Booking</h2>
      <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
      <p><strong>Trip:</strong> {booking.trip_type} / {booking.transport_type}</p>
      <p><strong>Fare:</strong> EUR {booking.price}</p>
      <p><strong>Booked At:</strong> {booking.created_at}</p>
      <p><strong>Fare:</strong> EUR {booking.price}</p>
        <p><strong>Pickup Address:</strong>  {booking.pickup_location_1}</p>
        <p><strong>Dropoff Address:</strong> {booking.dropoff_address}</p>
        <p><strong>Email:</strong> {booking.email}</p>
        <p><strong>Flight Number:</strong>  {booking.flight_number}</p>
        <p><strong>Check-in date:</strong> {booking.checkin_date}</p>
    </body></html>
    """
    msg = EmailMultiAlternatives("🚨 New Booking Received", "Booking info",
                                 settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)

def booking_view(request):
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

                # If round trip and leg2 omitted, auto reverse
                if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
                    p2, d2 = d1, p1
                    pa2, da2 = da1, pa1  # reverse addresses if provided

                pax = _pax(cd.get("passengers") or 1)

                legs = [{"p": p1.id, "d": d1.id},]
                if cd.get("trip_type") == "Round Trip": legs.append({"p": p2.id, "d": d2.id})

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
                # keep summary addresses (outbound)
                booking.pickup_address = pa1
                booking.dropoff_address = da1
                booking.price = price
                booking.save()
                if hasattr(form, "save_m2m"): form.save_m2m()

                # Persist legs with per-leg addresses
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

                # Recalculate on model (applies promo/night again safely)
                booking.calculate_total_price(passengers_override=pax)

                send_user_confirmation_email(booking)
                send_admin_emails(booking)
                return render(request, "booking/booking_success.html", {"booking": booking})
            else:
                messages.error(request, "Please fix the errors in the form.")
                logger.warning(f"Form errors: {form.errors}")
        except Exception as e:
            logger.error(f"Error during booking: {e}", exc_info=True)
            messages.error(request, "Something went wrong while processing your booking.")
    return render(request, "url/bookingpage.html", {
        "form": form,
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    })

# views.py


# app/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from .models import Location, PriceMatrix, PricingRule, PromoCode

@require_GET
def booking_quote_view(request):
    try:
        trip_type = request.GET.get("trip_type", "One Way")
        transport_type = request.GET.get("transport_type", "Car")
        pax = int(request.GET.get("passengers", 1))

        p1 = request.GET.get("pickup_location_1")
        d1 = request.GET.get("dropoff_location_1")
        p2 = request.GET.get("pickup_location_2")
        d2 = request.GET.get("dropoff_location_2")

        pickup_time = request.GET.get("pickup_time")      # "0" or "1" or ""
        return_time = request.GET.get("return_time")      # "0" or "1" or ""
        promo = (request.GET.get("promo_code") or "").strip()

        # must have leg 1
        if not (p1 and d1):
            return JsonResponse({"error": "missing_leg1", "price": None})

        p1 = int(p1); d1 = int(d1)
        p2 = int(p2) if p2 else None
        d2 = int(d2) if d2 else None

        total = 0.0

        def find_price(tt, o, de):
            qs = PriceMatrix.objects.filter(
                trip_type=tt,
                transport_type=transport_type,
                pax_min__lte=pax,
                pax_max__gte=pax
            )
            if tt == "One Way":
                row = qs.filter(origin_id=o, destination_id=de).first()
            else:
                a, b = sorted([o, de])
                row = qs.filter(origin_id=a, destination_id=b).first()
            return float(row.price) if row else 0.0

        if trip_type == "Round Trip" and p2 and d2:
            # if perfect reverse, prefer the roundtrip table
            if p1 == d2 and d1 == p2:
                total += find_price("Round Trip", p1, d1)
            else:
                total += find_price("One Way", p1, d1)
                total += find_price("One Way", p2, d2)
        else:
            total += find_price("One Way", p1, d1)

        # night charges
        rule = PricingRule.objects.filter(active=True).first()
        night = float(rule.night_charge) if rule and rule.night_charge else 0.0
        if night > 0:
            if pickup_time == "0":
                total += night
            if trip_type == "Round Trip" and return_time == "0":
                total += night

        # promo
        if promo:
            pc = PromoCode.objects.filter(code__iexact=promo, active=True).first()
            if pc and pc.valid_from <= timezone.now() <= pc.valid_until:
                total -= (pc.discount_percentage / 100.0) * total

        total = round(max(total, 0.0), 2)
        return JsonResponse({"price": total})
    except Exception as e:
        return JsonResponse({"error": "server_error", "detail": str(e), "price": None}, status=400)
