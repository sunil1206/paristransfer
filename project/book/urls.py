from django.urls import path
from .views import booking_view, booking_quote_view

urlpatterns = [
    path("booking/", booking_view, name="booking"),
    path("booking/quote/", booking_quote_view, name="booking_quote"),
]
