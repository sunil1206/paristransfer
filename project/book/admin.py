from django.contrib import admin
from .models import (
    Location, MainLocation, DetailedLocation, PromoCode, PricingRule,
    PriceMatrix, Booking, TripLeg
)

# --- The Fix: A Hidden Admin for the Base Location Model ---
# This class provides the necessary search functionality for autocomplete_fields
# to work across the admin site. We hide it from the admin index to avoid clutter.
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ('name', 'parent__name')

    def has_module_permission(self, request):
        # This returns False to hide the model from the admin index.
        return False

# --- Inlines ---

class DetailedLocationInline(admin.TabularInline):
    model = Location
    fk_name = 'parent'
    extra = 1
    verbose_name = "Detailed Location"
    verbose_name_plural = "Detailed Locations (Hotels, Stations, etc.)"
    autocomplete_fields = ('parent',) # This will now work

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'is_main_location':
            kwargs['initial'] = False
        return super().formfield_for_dbfield(db_field, request, **kwargs)

class TripLegInline(admin.TabularInline):
    model = TripLeg
    extra = 0
    fields = ('sequence', 'pickup_location', 'dropoff_location', 'pickup_address', 'dropoff_address')
    readonly_fields = ('sequence',)
    autocomplete_fields = ('pickup_location', 'dropoff_location') # This will now work
    can_delete = False

# --- Proxy Model Admins for Convenient Management ---

@admin.register(MainLocation)
class MainLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [DetailedLocationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_main_location=True)

    def save_model(self, request, obj, form, change):
        obj.is_main_location = True
        super().save_model(request, obj, form, change)

@admin.register(DetailedLocation)
class DetailedLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name', 'parent__name')
    list_filter = ('parent',)
    autocomplete_fields = ('parent',) # This will now work

    def save_model(self, request, obj, form, change):
        obj.is_main_location = False
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_main_location=False)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Location.objects.filter(is_main_location=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --- Other Model Admins ---

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_until', 'active')
    list_editable = ('active',)
    search_fields = ('code',)

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'night_charge', 'active')
    list_editable = ('active', 'night_charge')

@admin.register(PriceMatrix)
class PriceMatrixAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'trip_type', 'transport_type', 'pax_range', 'price')
    list_filter = ('trip_type', 'transport_type')
    search_fields = ('origin__name', 'destination__name')
    autocomplete_fields = ('origin', 'destination') # This will now work
    list_per_page = 20

    def pax_range(self, obj):
        return f"{obj.pax_min} - {obj.pax_max}"
    pax_range.short_description = 'Passengers'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'trip_summary', 'price', 'trip_type', 'created_at')
    list_filter = ('trip_type', 'transport_type', 'created_at', 'pickup_location')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('price', 'created_at')
    inlines = [TripLegInline]
    fieldsets = (
        ('Trip Summary', {'fields': ('trip_type', 'transport_type', 'pickup_location', 'dropoff_location', 'price', 'created_at')}),
        ('Contact Information', {'fields': ('first_name', 'last_name', 'email', ('country_code', 'phone'))}),
        ('Passenger & Flight Details', {'fields': (('adults', 'children', 'luggage'), 'flight_number', 'booster_seats')}),
        ('Dates & Times', {'fields': ('checkin_date', 'pickup_time', 'checkout_date', 'return_time')}),
        ('Additional Info', {'fields': ('promo_code', 'notes')}),
    )

    def customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'Customer'

    def trip_summary(self, obj):
        return f"{obj.pickup_location} → {obj.dropoff_location}"
    trip_summary.short_description = 'Route'