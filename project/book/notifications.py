# your_app/notifications.py
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_user_confirmation_email(booking):
    """Sends a confirmation email to the user using a Django template."""
    subject = f"Booking Confirmation: Your Transfer Details (Ref: PDT{booking.id})"
    leg1 = booking.legs.filter(sequence=1).first()

    # ✅ FIX: Prevents a crash if the main trip leg doesn't exist.
    if not leg1:
        logger.error(f"Cannot send user email for booking {booking.id}: First leg is missing.")
        return

    context = {
        'booking': booking,
        'leg1': leg1,
        'leg2': booking.legs.filter(sequence=2).first(),
        'pickup_time_formatted': booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else 'N/A',
        'return_time_formatted': booking.return_time.strftime('%I:%M %p') if booking.return_time else 'N/A',
        'total_passengers': (booking.adults or 0) + (booking.children or 0),
    }

    html_content = render_to_string('emails/user_confirmation.html', context)
    text_content = f"Hello {booking.first_name}, your booking PDT{booking.id} is confirmed."

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [booking.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_admin_emails(booking):
    """Sends a simple notification email to the admin."""
    subject = f"🚨 New Booking Received: PDT{booking.id} from {booking.first_name}"
    body = f"New booking PDT{booking.id} for {booking.first_name} {booking.last_name} has been received. Please check the admin panel for full details."
    msg = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, settings.ADMIN_EMAILS)
    msg.send()


def send_sms_notifications(booking):
    """Sends SMS notifications to user and admin via Twilio."""
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    twilio_phone = getattr(settings, "TWILIO_PHONE_NUMBER", None)
    admin_phone = getattr(settings, "ADMIN_PHONE_NUMBER", None)

    if not all([account_sid, auth_token, twilio_phone]):
        logger.error("Twilio settings are not configured. SMS not sent.")
        return

    leg1 = booking.legs.filter(sequence=1).first()
    # ✅ FIX: Prevents a crash if the main trip leg doesn't exist.
    if not leg1:
        logger.error(f"Cannot send SMS for booking {booking.id}: First leg is missing.")
        return

    try:
        client = Client(account_sid, auth_token)
        ptf = booking.pickup_time.strftime('%I:%M %p') if booking.pickup_time else ''

        user_message = (
            f"Hi {booking.first_name}, your booking PDT{booking.id} is confirmed! "
            f"From {leg1.pickup_location.name} to {leg1.dropoff_location.name} at {ptf}. "
            f"Total: €{booking.price}. Thank you!"
        )
        to_number = f"+{booking.country_code}{booking.phone}"
        client.messages.create(body=user_message, from_=twilio_phone, to=to_number)

        if admin_phone:
            admin_message = (
                f"New Booking: PDT{booking.id} - {booking.first_name} {booking.last_name}, "
                f"{leg1.pickup_location.name} -> {leg1.dropoff_location.name}, "
                f"Time: {ptf}, Pax: {(booking.adults or 0) + (booking.children or 0)}, €{booking.price}"
            )
            client.messages.create(body=admin_message, from_=twilio_phone, to=admin_phone)

    except Exception as e:
        logger.error(f"Failed to send Twilio SMS for booking {booking.id}: {e}", exc_info=True)