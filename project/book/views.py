import logging
from datetime import time, datetime
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from twilio.rest import Client

from .forms import BookingForm
from .models import TripLeg, PriceMatrix, PricingRule, PromoCode, Location, find_matrix_price

logger = logging.getLogger(__name__)


#
# # --- Notification Functions ---
# def send_user_confirmation_email(booking):
#     subject = f"Booking Confirmation: Your Transfer Details"
#     leg1 = booking.legs.filter(sequence=1).first()
#     leg2 = booking.legs.filter(sequence=2).first()
#     pickup_time_formatted = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else 'N/A'
#     return_time_formatted = booking.return_time.strftime('%I:%M %p') if leg2 and booking.return_time else 'N/A'
#     html_content = f"""
#     <!DOCTYPE html><html><head><meta charset="utf-8"><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0;padding:0;background-color:#f4f7fc}}.container{{width:100%;max-width:600px;margin:20px auto;background-color:#fff;border-radius:12px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,.05)}}.header{{background-color:#4A90E2;color:#fff;padding:40px;text-align:center}}.header h1{{margin:0;font-size:28px}}.content{{padding:30px;line-height:1.6}}.content h2{{color:#333;border-bottom:2px solid #f0f0f0;padding-bottom:10px;margin-top:0;font-size:20px}}.details-grid{{margin-top:20px}}.detail-item{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0}}.detail-item dt{{color:#666;font-weight:700}}.detail-item dd{{margin:0;color:#333;text-align:right}}.total{{font-size:24px;font-weight:700;color:#4A90E2}}.footer{{background-color:#f8f9fa;text-align:center;padding:20px;font-size:12px;color:#888}}</style></head><body><div class="container"><div class="header"><h1>Booking Confirmed!</h1></div><div class="content"><h2>Hello {booking.first_name},</h2><p>Thank you for your booking. Your transfer details are confirmed below:</p><h2>Trip Summary</h2><div class="details-grid"><div class="detail-item"><dt>Total Price:</dt><dd><strong class="total">&euro;{booking.price}</strong></dd></div><div class="detail-item"><dt>Trip Type:</dt><dd>{booking.trip_type}</dd></div>
#     <div class="detail-item"><dt>Transport:</dt><dd>{booking.transport_type}</dd></div><div class="detail-item"><dt>Passengers:</dt><dd>{booking.total_passengers()}</dd></div></div><h2>Outbound Leg</h2><div class="details-grid"><div class="detail-item"><dt>Pickup:</dt><dd>{leg1.pickup_location}</dd></div><div class="detail-item"><dt>Drop-off:</dt><dd>{leg1.dropoff_location}</dd></div><div class="detail-item"><dt>Pickup Time:</dt><dd>{pickup_time_formatted}</dd></div><div class="detail-item"><dt>Pickup Address:</dt><dd>{leg1.pickup_address or 'N/A'}</dd></div></div>
#     {f'''<h2>Return Leg</h2><div class="details-grid"><div class="detail-item"><dt>Pickup:</dt><dd>{leg2.pickup_location}</dd></div><div class="detail-item"><dt>Drop-off:</dt><dd>{leg2.dropoff_location}</dd></div><div class="detail-item"><dt>Return Time:</dt><dd>{return_time_formatted}</dd></div><div class="detail-item"><dt>Return Address:</dt><dd>{leg2.pickup_address or 'N/A'}</dd></div></div>''' if leg2 else ''}
#     </div><div class="footer"><p>Thank you for choosing our service. If you have any questions, please contact us.</p></div></div></body></html>
#     """
#     plain_text_content = f"Hello {booking.first_name}, your booking is confirmed. Total Price: €{booking.price}."
#     msg = EmailMultiAlternatives(subject, plain_text_content, settings.DEFAULT_FROM_EMAIL, [booking.email])
#     msg.attach_alternative(html_content, "text/html")
#     msg.send(fail_silently=False)
#
#
# def send_admin_emails(booking):
#     subject = f"🚨 New Booking Received from {booking.first_name} {booking.last_name}"
#     leg1 = booking.legs.filter(sequence=1).first()
#     leg2 = booking.legs.filter(sequence=2).first()
#     pickup_time_formatted = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else 'N/A'
#     return_time_formatted = booking.return_time.strftime('%I:%M %p') if leg2 and booking.return_time else 'N/A'
#     html_content = f"""
#     <h3>New Booking Details:</h3><ul><li><strong>Name:</strong> {booking.first_name} {booking.last_name}</li><li><strong>Email:</strong> {booking.email}</li><li><strong>Phone:</strong> +{booking.country_code} {booking.phone}</li><li><strong>Total Price:</strong> &euro;{booking.price}</li><li><strong>Trip Type:</strong> {booking.trip_type}</li><li><strong>Transport:</strong> {booking.transport_type}</li><li><strong>Passengers:</strong> {booking.adults} Adults, {booking.children} Children</li><li><strong>Luggage:</strong> {booking.luggage}</li><li><strong>Outbound:</strong> {leg1.pickup_location} to {leg1.dropoff_location}</li><li><strong>Pickup Time:</strong> {pickup_time_formatted}</li>
#     {f'<li><strong>Return:</strong> {leg2.pickup_location} to {leg2.dropoff_location}</li>' if leg2 else ''}{f'<li><strong>Return Time:</strong> {return_time_formatted}</li>' if leg2 else ''}<li><strong>Notes:</strong> {booking.notes or 'None'}</li></ul>
#     """
#     msg = EmailMultiAlternatives(subject, "New booking received.", settings.DEFAULT_FROM_EMAIL,
#                                  [settings.DEFAULT_FROM_EMAIL])
#     msg.attach_alternative(html_content, "text/html")
#     msg.send(fail_silently=False)
#
#
# def send_sms_notifications(booking):
#     account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
#     auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
#     twilio_phone = getattr(settings, "TWILIO_PHONE_NUMBER", None)
#     admin_phone = getattr(settings, "ADMIN_PHONE_NUMBER", None)
#     if not all([account_sid, auth_token, twilio_phone]):
#         logger.error("Twilio settings are not configured. SMS not sent.")
#         return
#     try:
#         client = Client(account_sid, auth_token)
#         leg1 = booking.legs.filter(sequence=1).first()
#         ptf = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else ''
#         user_message = (
#             f"Hi {booking.first_name}, your booking is confirmed! From {leg1.pickup_location.name} to {leg1.dropoff_location.name} at {ptf}. Total: €{booking.price}. Thank you!")
#         client.messages.create(body=user_message, from_=twilio_phone, to=f"+{booking.country_code}{booking.phone}")
#         if admin_phone:
#             admin_message = (
#                 f"New Booking: {booking.first_name} {booking.last_name}, {leg1.pickup_location.name} -> {leg1.dropoff_location.name}, Time: {ptf}, Pax: {booking.total_passengers()}, €{booking.price}")
#             client.messages.create(body=admin_message, from_=twilio_phone, to=admin_phone)
#     except Exception as e:
#         logger.error(f"Failed to send Twilio SMS: {e}", exc_info=True)


def send_user_confirmation_email(booking):
    """Sends a detailed HTML confirmation email to the user, matching the new design."""
    subject = f"Booking Confirmation: PDT{booking.id}"
    leg1 = booking.legs.filter(sequence=1).first()
    leg2 = booking.legs.filter(sequence=2).first()

    # Format dates and times for display
    pickup_date_formatted = booking.checkin_date.strftime('%d/%m/%Y') if booking.checkin_date else 'N/A'
    pickup_time_formatted = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else 'N/A'
    return_date_formatted = booking.checkout_date.strftime('%d/%m/%Y') if leg2 and booking.checkout_date else 'N/A'
    return_time_formatted = booking.return_time.strftime('%I:%M %p') if leg2 and booking.return_time else 'N/A'

    # Combine adults and children for total passengers
    total_passengers = (booking.adults or 0) + (booking.children or 0)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Booking Confirmation</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
                color: #333;
            }}
            .email-container {{
                max-width: 600px;
                margin: auto;
                background: #ffffff;
                padding: 20px;
                border: 1px solid #ddd;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header img {{
                max-width: 200px;
                margin-bottom: 10px;
            }}
            h2 {{
                font-size: 14px;
                color: #555;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
                margin-top: 20px;
                margin-bottom: 10px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            p {{
                line-height: 1.6;
                margin: 5px 0;
            }}
            strong {{
                display: inline-block;
                width: 150px; /* Adjust width as needed */
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <!-- IMPORTANT: Replace this placeholder with the actual URL to your logo -->
                <img src="https://www.parismagiclandtransfer.com/static/img/logo4.png" alt="Paris Disney Transfer Logo">
                <p><strong>Booking no:</strong> PDT{booking.id}</p>
                <p><strong>Date:</strong> {booking.created_at.strftime('%d/%m/%Y')}</p>
                <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
                <p><strong>Phone no:</strong> +{booking.country_code} {booking.phone}</p>
                <p><strong>E-mail:</strong> {booking.email}</p>
                <p><strong>Total Price:</strong> {booking.price}</p>
            </div>

            <h2>Journey Type: {booking.trip_type}</h2>

            <p><strong>PICK UP FROM:</strong> {leg1.pickup_location}</p>
            <p><strong>DESTINATION:</strong> {leg1.dropoff_location}</p>
            <p><strong>No of passengers:</strong> {total_passengers}</p>

            <p><strong>Pickup Address:</strong> {leg1.pickup_address}</p>
        <p><strong> Drop-off:</strong> {leg1.dropoff_address}</p>
        <p><strong>Outbound Time:</strong> {pickup_date_formatted} at {pickup_time_formatted}</p>
        {f'''<hr>
        <p><strong>Return Pickup:</strong> {leg2.pickup_address}</p>
        <p><strong>Return Drop-off:</strong> {leg2.dropoff_address}</p>
        <p><strong>Return Time:</strong> {return_date_formatted} at {return_time_formatted}</p>
        ''' if leg2 else ''}

            <p><strong>Flight/Train no:</strong> {booking.flight_number or 'N/A'}</p>
            <p><strong>Luggage:</strong> {booking.luggage or 0}</p>
            <p><strong>Baby seats:</strong> {booking.baby_seats or 0}</p> <!-- You don't have a baby_seats field, so this is a placeholder -->
            <p><strong>Boosters:</strong> {booking.booster_seats or 0}</p>
            <p><strong>Notes:</strong> {booking.notes or 'None'}</p>
        </div>
    </body>
    </html>
    """
    plain_text_content = f"Hello {booking.first_name}, your booking PDT{booking.id} is confirmed."
    msg = EmailMultiAlternatives(subject, plain_text_content, settings.DEFAULT_FROM_EMAIL, [booking.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_admin_emails(booking):
    """Sends an attractive HTML notification email to the admin."""
    subject = f"🚨 New Booking Received: {booking.id} from {booking.first_name} {booking.last_name}"
    leg1 = booking.legs.filter(sequence=1).first()
    leg2 = booking.legs.filter(sequence=2).first()

    # ✅ FIX: Added a safety check to prevent crashes if the first leg is missing.
    if not leg1:
        logger.error(f"Cannot send admin email for booking {booking.id}: First leg is missing.")
        return

    # --- Prepare data for the template ---
    pickup_date_formatted = booking.checkin_date.strftime('%d %B %Y') if booking.checkin_date else 'N/A'
    pickup_time_formatted = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else 'N/A'
    return_date_formatted = booking.checkout_date.strftime('%d %B %Y') if leg2 and booking.checkout_date else 'N/A'
    return_time_formatted = booking.return_time.strftime('%I:%M %p') if leg2 and booking.return_time else 'N/A'
    total_passengers = (booking.adults or 0) + (booking.children or 0)

    # --- ✨ Attractive HTML Email Template ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Booking Notification</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f7f9;">
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #f4f7f9;">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                        <tr>
                            <td align="center" style="background-color: #dc3545; color: #ffffff; padding: 25px; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 600;">🚨 New Booking Received</h1>
                                <p style="margin: 5px 0 0; font-size: 16px;">Booking ID: {booking.id}</p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 30px 25px;">
                                <h2 style="font-size: 18px; margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">Contact & Price</h2>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Name:</strong> {booking.first_name} {booking.last_name}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Email:</strong> {booking.email}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Phone:</strong> {booking.phone}</p>
                                <p style="margin: 8px 0; font-size: 18px; color: #0d6efd;"><strong style="display: inline-block; width: 120px; color: #111;">Total Price:</strong> &euro;{booking.price}</p>

                                <h2 style="font-size: 18px; margin: 30px 0 15px 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">Trip Details</h2>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Trip Type:</strong> {booking.trip_type}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Transport:</strong> {booking.transport_type}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Passengers:</strong> {total_passengers} ({booking.adults} Adults, {booking.children} Children)</p>

                                <h2 style="font-size: 18px; margin: 30px 0 15px 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">Journey Legs</h2>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Outbound From:</strong> {leg1.pickup_location}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Outbound To:</strong> {leg1.dropoff_location}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Outbound Time:</strong> {pickup_date_formatted} at {pickup_time_formatted}</p>

                                {f'''
                                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                                    <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Return From:</strong> {leg2.pickup_location}</p>
                                    <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Return To:</strong> {leg2.dropoff_location}</p>
                                    <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Return Time:</strong> {return_date_formatted} at {return_time_formatted}</p>
                                </div>
                                ''' if leg2 else ''}

                                <h2 style="font-size: 18px; margin: 30px 0 15px 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">Additional Info</h2>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Flight Number:</strong> {booking.flight_number or 'N/A'}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Luggage:</strong> {booking.luggage or 0}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Booster Seats:</strong> {booking.booster_seats or 0}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Baby Seats:</strong> {booking.baby_seats or 0}</p>
                                <p style="margin: 8px 0; font-size: 16px; color: #555;"><strong style="display: inline-block; width: 120px; color: #111;">Notes:</strong></p>
                                <p style="margin: 5px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-size: 15px; color: #444;">{booking.notes or 'None'}</p>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding: 20px; font-size: 12px; color: #888; border-top: 1px solid #eee;">
                                <p style="margin: 0;">This is an automated notification from your website.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # --- Send the email ---
    # The plain text version is a simple fallback.
    plain_text_content = f"New booking received from {booking.first_name} {booking.last_name}. ID: {booking.id}. Price: €{booking.price}."

    msg = EmailMultiAlternatives(
        subject,
        plain_text_content,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMIN_EMAILS  #  Sends to the admin list from your settings
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_sms_notifications(booking):
    # This function remains unchanged but will work with the rest of the flow.
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    twilio_phone = getattr(settings, "TWILIO_PHONE_NUMBER", None)
    admin_phone = getattr(settings, "ADMIN_PHONE_NUMBER", None)
    if not all([account_sid, auth_token, twilio_phone]):
        logger.error("Twilio settings are not configured. SMS not sent.")
        return
    try:
        client = Client(account_sid, auth_token)
        leg1 = booking.legs.filter(sequence=1).first()
        ptf = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else ''
        user_message = (
            f"Hi {booking.first_name}, your booking PDT{booking.id} is confirmed! From {leg1.pickup_location.name} to {leg1.dropoff_location.name} at {ptf}. Total: €{booking.price}. Thank you!")
        client.messages.create(body=user_message, from_=twilio_phone, to=f"+{booking.country_code}{booking.phone}")
        if admin_phone:
            admin_message = (
                f"New Booking: PDT{booking.id} - {booking.first_name} {booking.last_name}, {leg1.pickup_location.name} -> {leg1.dropoff_location.name}, Time: {ptf}, Pax: {booking.total_passengers()}, €{booking.price}")
            client.messages.create(body=admin_message, from_=twilio_phone, to=admin_phone)
    except Exception as e:
        logger.error(f"Failed to send Twilio SMS: {e}", exc_info=True)


# --- Main Views ---
def booking_view(request):
    form = BookingForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                cd = form.cleaned_data
                tp = cd.get("adults", 1) + cd.get("children", 0)
                p1, d1 = cd["pickup_location_1"], cd["dropoff_location_1"]
                pa1, da1 = cd.get("pickup_address_1", ""), cd.get("dropoff_address_1", "")
                p2, d2 = cd.get("pickup_location_2"), cd.get("dropoff_location_2")
                pa2, da2 = cd.get("pickup_address_2", ""), cd.get("dropoff_address_2", "")
                if cd.get("trip_type") == "Round Trip" and (not p2 or not d2):
                    p2, d2 = d1, p1;
                    pa2, da2 = da1, pa1
                booking = form.save(commit=False)
                booking.pickup_location = p1;
                booking.dropoff_location = d1
                booking.pickup_address = pa1;
                booking.dropoff_address = da1
                booking.save()
                TripLeg.objects.create(booking=booking, sequence=1, pickup_location=p1, dropoff_location=d1,
                                       pickup_address=pa1, dropoff_address=da1)
                if cd.get("trip_type") == "Round Trip":
                    TripLeg.objects.create(booking=booking, sequence=2, pickup_location=p2, dropoff_location=d2,
                                           pickup_address=pa2, dropoff_address=da2)

                # ✅ FIXED: The argument name is now correct.
                booking.calculate_total_price(passengers_override=tp)

                send_user_confirmation_email(booking);
                send_admin_emails(booking);
                send_sms_notifications(booking)
                return render(request, "booking/booking_success.html", {"booking": booking})
            except Exception as e:
                logger.error(f"Error during booking submission: {e}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            logger.warning(f"Booking form validation errors: {form.errors.as_json()}")
            messages.error(request, "Please correct the errors below.")
    main_locations = Location.objects.filter(is_main_location=True).annotate(
        sub_location_count=Count('sub_locations')).order_by('name')
    return render(request, "url/bookingpage.html", {"form": form, "main_locations": main_locations,
                                                    "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY",
                                                                                   "")})


# --- API Views ---
@require_GET
def get_sub_locations(request):
    parent_id = request.GET.get("parent_id")
    if not parent_id: return JsonResponse({"error": "Parent ID is required"}, status=400)
    try:
        locations = Location.objects.filter(parent_id=parent_id).values("id", "name")
        return JsonResponse(list(locations), safe=False)
    except Exception as e:
        logger.error(f"Error fetching sub-locations: {e}")
        return JsonResponse({"error": "server_error"}, status=500)


@require_GET
def booking_quote_view(request):
    try:
        tt, trt, pax = request.GET.get("trip_type", "One Way"), request.GET.get("transport_type", "Car"), int(
            request.GET.get("passengers", 1))
        p1_id, d1_id = request.GET.get("pickup_location_1"), request.GET.get("dropoff_location_1")
        if not (p1_id and d1_id): return JsonResponse({"error": "missing_leg1", "price": None})
        total = 0.0
        if tt == "Round Trip":
            p2_id, d2_id = request.GET.get("pickup_location_2"), request.GET.get("dropoff_location_2")
            if str(p1_id) == str(d2_id) and str(d1_id) == str(p2_id):
                total = find_matrix_price("Round Trip", trt, int(p1_id), int(d1_id), pax)
            else:
                total += find_matrix_price("One Way", trt, int(p1_id), int(d1_id), pax)
                if p2_id and d2_id: total += find_matrix_price("One Way", trt, int(p2_id), int(d2_id), pax)
        else:
            total = find_matrix_price("One Way", trt, int(p1_id), int(d1_id), pax)
        rule = PricingRule.objects.filter(active=True).first()
        nc = float(rule.night_charge) if rule and rule.night_charge else 0.0
        if nc > 0:
            ns, ne = time(22, 0), time(6, 0)
            pts = request.GET.get("pickup_time");
            rts = request.GET.get("return_time")
            if pts:
                pt = datetime.strptime(pts, '%H:%M').time()
                if pt >= ns or pt < ne: total += nc
            if tt == "Round Trip" and rts:
                rt = datetime.strptime(rts, '%H:%M').time()
                if rt >= ns or rt < ne: total += nc
        pcs = request.GET.get("promo_code", "").strip()
        if pcs:
            promo = PromoCode.objects.filter(code__iexact=pcs, active=True, valid_from__lte=timezone.now(),
                                             valid_until__gte=timezone.now()).first()
            if promo: total -= (promo.discount_percentage / 100.0) * total
        return JsonResponse({"price": round(max(total, 0.0), 2)})
    except Exception as e:
        logger.error(f"Quote calculation error: {e}")
        return JsonResponse({"error": "server_error"}, status=400)

