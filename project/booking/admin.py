from django.contrib import admin
from .models import Booking,TaxiData

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'trip_type', 'pickup_location', 'dropoff_location', 'transport_type', 'adults', 'children', 'luggage', 'pickup_time', 'return_time', 'email', 'phone', 'notes')
    search_fields = ('first_name', 'last_name', 'trip_type', 'pickup_location', 'dropoff_location', 'transport_type', 'email', 'phone')

@admin.register(TaxiData)
class TaxiDataAdmin(admin.ModelAdmin):
    list_display = ( 'trip_type', 'pickup_location', 'dropoff_location', 'transport_type', 'adults', 'children', 'pickup_time', 'return_time','price')
    search_fields = ('trip_type', 'pickup_location', 'dropoff_location', 'transport_type','price')
