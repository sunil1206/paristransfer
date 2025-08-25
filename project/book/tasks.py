# app/tasks.py

import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import Booking  # Make sure to import your Booking model

logger = logging.getLogger(__name__)

def _send_user_confirmation_email(booking):
    """Helper function to build and send the user confirmation email."""
    subject = "Booking Confirmation – Your Ride is Booked!"
    plain = f"Dear {booking.first_name}, your booking is confirmed. Fare: EUR {booking.price}."
    html = f"""
    <html><body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
      <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #4CAF50; border-bottom: 2px solid #eeeeee; padding-bottom: 10px;">🚖 Booking Confirmed</h2>
        <p>Hello <strong>{booking.first_name}</strong>,</p>
        <p>Thank you for booking with us. Your trip details are below:</p>
        <p><strong>Fare:</strong> EUR {booking.price}</p>
        <p><strong>Trip Type:</strong> {booking.trip_type}</p>
        <p><strong>Transport:</strong> {booking.transport_type}</p>
        <p><strong>Pickup Address:</strong> {booking.pickup_address}</p>
        <p><strong>Dropoff Address:</strong> {booking.dropoff_address}</p>
        <p><strong>Email:</strong> {booking.email}</p>
        <p><strong>Flight Number:</strong> {booking.flight_number or 'N/A'}</p>
        <p><strong>Check-in date:</strong> {booking.checkin_date}</p>
      </div>
    </body></html>
    """
    try:
        send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, [booking.email], html_message=html, fail_silently=False)
        logger.info(f"Successfully sent confirmation email for booking ID: {booking.id}")
    except Exception as e:
        logger.error(f"Error sending user confirmation email for booking ID {booking.id}: {e}", exc_info=True)
        raise  # Re-raise the exception so Celery can retry it


def _send_admin_notification_email(booking):
    """Helper function to build and send the admin notification email."""
    # Note: Corrected the placeholder for pickup_location_1 to use booking.pickup_address for consistency.
    html = f"""
    <html><body>
      <h2>🚨 New Booking Received</h2>
      <p><strong>Name:</strong> {booking.first_name} {booking.last_name}</p>
      <p><strong>Trip:</strong> {booking.trip_type} / {booking.transport_type}</p>
      <p><strong>Fare:</strong> EUR {booking.price}</p>
      <p><strong>Booked At:</strong> {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
      <p><strong>Pickup Address:</strong> {booking.pickup_address}</p>
      <p><strong>Dropoff Address:</strong> {booking.dropoff_address}</p>
      <p><strong>Email:</strong> {booking.email}</p>
      <p><strong>Flight Number:</strong> {booking.flight_number or 'N/A'}</p>
      <p><strong>Check-in date:</strong> {booking.checkin_date}</p>
    </body></html>
    """
    try:
        msg = EmailMultiAlternatives(
            "🚨 New Booking Received",
            f"New booking from {booking.first_name} {booking.last_name}. Fare: EUR {booking.price}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL]
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Successfully sent admin notification for booking ID: {booking.id}")
    except Exception as e:
        logger.error(f"Error sending admin notification for booking ID {booking.id}: {e}", exc_info=True)
        raise # Re-raise the exception so Celery can retry it


@shared_task(bind=True, max_retries=3, default_retry_delay=300) # Retry 3 times, waiting 5 mins between failures
def send_booking_emails_task(self, booking_id):
    """
    Celery background task to send both user and admin emails.
    It will retry automatically if the email server fails temporarily.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        _send_user_confirmation_email(booking)
        _send_admin_notification_email(booking)
    except Booking.DoesNotExist:
        logger.warning(f"Booking ID {booking_id} not found. Cannot send emails.")
    except Exception as exc:
        logger.error(f"Failed to send emails for booking ID {booking_id}. Retrying...")
        raise self.retry(exc=exc)