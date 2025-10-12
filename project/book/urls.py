from django.urls import path

from . import views
from .views import booking_view, booking_quote_view

urlpatterns = [
    path("booking/", booking_view, name="booking"),
    path("booking/quote/", booking_quote_view, name="booking_quote"),

    # API endpoint for fetching sub-locations (e.g., specific hotels)
    path('api/get-sub-locations/', views.get_sub_locations, name='get_sub_locations'),

]
