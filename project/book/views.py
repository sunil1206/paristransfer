# app/views.py
import logging
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import BookingForm
from .models import TripLeg, PriceMatrix, PricingRule, PromoCode, find_matrix_price

logger = logging.getLogger(__name__)


# --- Email Sending Functions ---

def send_user_confirmation_email(booking):
    """
    Sends an attractive and detailed HTML email to the user upon successful booking.
    """
    subject = f"Booking Confirmation: Your Transfer to {booking.dropoff_location.name}"

    # Get the trip legs for detailed information in the email
    leg1 = booking.legs.filter(sequence=1).first()
    leg2 = booking.legs.filter(sequence=2).first()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f7fc; }}
            .container {{ width: 100%; max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 6px 20px rgba(0,0,0,0.05); }}
            .header {{ background-color: #4A90E2; color: white; padding: 40px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .content {{ padding: 30px; line-height: 1.6; }}
            .content h2 {{ color: #333; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; margin-top: 0; font-size: 20px; }}
            .details-grid {{ margin-top: 20px; }}
            .detail-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
            .detail-item dt {{ color: #666; font-weight: bold; }}
            .detail-item dd {{ margin: 0; color: #333; text-align: right; }}
            .total {{ font-size: 24px; font-weight: bold; color: #4A90E2; }}
            .footer {{ background-color: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Booking Confirmed!</h1></div>
            <div class="content">
                <h2>Hello {booking.first_name},</h2>
                <p>Thank you for your booking. Your transfer details are confirmed below:</p>

                <h2>Trip Summary</h2>
                <div class="details-grid">
                    <div class="detail-item"><dt>Total Price:</dt><dd><strong class="total">&euro;{booking.price}</strong></dd></div>
                    <div class="detail-item"><dt>Trip Type:</dt><dd>{booking.trip_type}</dd></div>
                    <div class="detail-item"><dt>Transport:</dt><dd>{booking.transport_type}</dd></div>
                    <div class="detail-item"><dt>Passengers:</dt><dd>{booking.total_passengers()}</dd></div>
                </div>

                <h2>Outbound Leg</h2>
                <div class="details-grid">
                    <div class="detail-item"><dt>Pickup:</dt><dd>{leg1.pickup_location.name}</dd></div>
                    <div class="detail-item"><dt>Drop-off:</dt><dd>{leg1.dropoff_location.name}</dd></div>
                    <div class="detail-item"><dt>Pickup Time:</dt><dd>{booking.get_pickup_time_display()}</dd></div>
                    <div class="detail-item"><dt>Pickup Address:</dt><dd>{leg1.pickup_address or 'N/A'}</dd></div>
                </div>

                {f'''<h2>Return Leg</h2>
                <div class="details-grid">
                    <div class="detail-item"><dt>Pickup:</dt><dd>{leg2.pickup_location.name}</dd></div>
                    <div class="detail-item"><dt>Drop-off:</dt><dd>{leg2.dropoff_location.name}</dd></div>
                    <div class="detail-item"><dt>Return Time:</dt><dd>{booking.get_return_time_display()}</dd></div>
                    <div class="detail-item"><dt>Return Address:</dt><dd>{leg2.pickup_address or 'N/A'}</dd></div>
                </div>''' if leg2 else ''}
            </div>
            <div class="footer">
                <p>Thank you for choosing our service. If you have any questions, please contact us.</p>
            </div>
        </div>
    </body>
    </html>
    """
    # The plain text version is a fallback for email clients that don't support HTML
    plain_text_content = f"Hello {booking.first_name}, your booking is confirmed. Total Price: €{booking.price}."
    msg = EmailMultiAlternatives(subject, plain_text_content, settings.DEFAULT_FROM_EMAIL, [booking.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_admin_emails(booking):
    """Sends a detailed notification email to the admin."""
    subject = f"🚨 New Booking Received from {booking.first_name} {booking.last_name}"
    leg1 = booking.legs.filter(sequence=1).first()
    leg2 = booking.legs.filter(sequence=2).first()

    html_content = f"""
    <h3>New Booking Details:</h3>
    <ul>
        <li><strong>Name:</strong> {booking.first_name} {booking.last_name}</li>
        <li><strong>Email:</strong> {booking.email}</li>
        <li><strong>Phone:</strong> +{booking.country_code} {booking.phone}</li>
        <li><strong>Total Price:</strong> &euro;{booking.price}</li>
        <li><strong>Trip Type:</strong> {booking.trip_type}</li>
        <li><strong>Transport:</strong> {booking.transport_type}</li>
        <li><strong>Passengers:</strong> {booking.adults} Adults, {booking.children} Children</li>
        <li><strong>Luggage:</strong> {booking.luggage}</li>
        <li><strong>Outbound:</strong> {leg1.pickup_location.name} to {leg1.dropoff_location.name}</li>
        <li><strong>Pickup Time:</strong> {booking.get_pickup_time_display()}</li>
        {f'<li><strong>Return:</strong> {leg2.pickup_location.name} to {leg2.dropoff_location.name}</li>' if leg2 else ''}
        {f'<li><strong>Return Time:</strong> {booking.get_return_time_display()}</li>' if leg2 else ''}
        <li><strong>Notes:</strong> {booking.notes or 'None'}</li>
    </ul>
    """
    msg = EmailMultiAlternatives(subject, "New booking received.", settings.DEFAULT_FROM_EMAIL,
                                 [settings.DEFAULT_FROM_EMAIL])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


# --- Main Booking View ---

def booking_view(request):
    form = BookingForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                cd = form.cleaned_data

                # FIX: Correctly calculate total passengers from the form's adults and children fields.
                total_passengers = cd.get("adults", 1) + cd.get("children", 0)

                # FIX: Correctly get all locations and addresses from the custom form fields.
                p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
                pa1, da1 = cd.get("pickup_address_1", ""), cd.get("dropoff_address_1", "")

                p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
                pa2, da2 = cd.get("pickup_address_2", ""), cd.get("dropoff_address_2", "")

                if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
                    p2, d2 = d1, p1
                    pa2, da2 = da1, pa1

                # --- Create Booking instance ---
                booking = form.save(commit=False)

                # Manually set the summary fields on the Booking model
                booking.pickup_location = p1
                booking.dropoff_location = d1
                booking.pickup_address = pa1
                booking.dropoff_address = da1
                booking.save()  # Save the booking object first to get an ID

                # --- Create TripLeg instances for detailed records ---
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

                # Recalculate the final price on the model to apply promo codes, etc.
                booking.calculate_total_price(passengers_override=total_passengers)

                # --- Send notifications ---
                send_user_confirmation_email(booking)
                send_admin_emails(booking)

                return render(request, "booking/booking_success.html", {"booking": booking})

            except Exception as e:
                logger.error(f"Error during booking submission: {e}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            logger.warning(f"Booking form validation errors: {form.errors.as_json()}")
            messages.error(request, "Please correct the errors below.")

    return render(request, "url/bookingpage.html", {
        "form": form,
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    })


# --- Quote View (for live pricing) ---

@require_GET
def booking_quote_view(request):
    try:
        trip_type = request.GET.get("trip_type", "One Way")
        transport_type = request.GET.get("transport_type", "Car")
        pax = int(request.GET.get("passengers", 1))
        p1_id = request.GET.get("pickup_location_1")
        d1_id = request.GET.get("dropoff_location_1")

        if not (p1_id and d1_id):
            return JsonResponse({"error": "missing_leg1", "price": None})

        # Base price calculation
        total = find_matrix_price(trip_type, transport_type, int(p1_id), int(d1_id), pax)

        # Add night charges
        rule = PricingRule.objects.filter(active=True).first()
        night_charge = float(rule.night_charge) if rule and rule.night_charge else 0.0
        if night_charge > 0:
            if request.GET.get("pickup_time") == "0": total += night_charge
            if trip_type == "Round Trip" and request.GET.get("return_time") == "0": total += night_charge

        # Apply promo code
        promo_code_str = request.GET.get("promo_code", "").strip()
        if promo_code_str:
            promo = PromoCode.objects.filter(
                code__iexact=promo_code_str,
                active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            ).first()
            if promo:
                total -= (promo.discount_percentage / 100.0) * total

        return JsonResponse({"price": round(max(total, 0.0), 2)})
    except Exception as e:
        logger.error(f"Quote calculation error: {e}")
        return JsonResponse({"error": "server_error", "price": None}, status=400)
