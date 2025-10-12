# your_app/tasks.py
import logging
from celery import shared_task
from .models import Booking
from .notifications import send_user_confirmation_email, send_admin_emails, send_sms_notifications

logger = logging.getLogger(__name__)

@shared_task
def send_all_notifications_task(booking_id):
    """Celery task to orchestrate all notifications for a new booking."""
    try:
        booking = Booking.objects.get(id=booking_id)
        # Call each notification function sequentially in the background
        send_user_confirmation_email(booking)
        send_admin_emails(booking)
        send_sms_notifications(booking)
    except Booking.DoesNotExist:
        logger.warning(f"Booking with ID {booking_id} not found for sending notifications.")
    except Exception as e:
        logger.error(f"An error occurred in the notification task for booking {booking_id}: {e}", exc_info=True)