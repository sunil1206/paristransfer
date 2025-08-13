# app/admin.py
from django.contrib import admin
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget, IntegerWidget, DecimalWidget

from .models import (
    Location,
    PromoCode,
    PricingRule,
    PriceMatrix,
    Booking,
    TripLeg,
)

# ---------------------------
# Import/Export resources
# ---------------------------

class PriceMatrixResource(resources.ModelResource):
    # Use Location names in CSV (human-friendly)
    origin = fields.Field(
        column_name="origin",
        attribute="origin",
        widget=ForeignKeyWidget(Location, "name"),
    )
    destination = fields.Field(
        column_name="destination",
        attribute="destination",
        widget=ForeignKeyWidget(Location, "name"),
    )
    pax_min = fields.Field(column_name="pax_min", attribute="pax_min", widget=IntegerWidget())
    pax_max = fields.Field(column_name="pax_max", attribute="pax_max", widget=IntegerWidget())
    price   = fields.Field(column_name="price",   attribute="price",   widget=DecimalWidget())

    class Meta:
        model = PriceMatrix
        fields = (
            "origin", "destination",
            "trip_type", "transport_type",
            "pax_min", "pax_max", "price",
        )
        export_order = (
            "origin", "destination",
            "trip_type", "transport_type",
            "pax_min", "pax_max", "price",
        )
        # natural key so re-import updates instead of duplicating
        import_id_fields = ("origin", "destination", "trip_type", "transport_type", "pax_min", "pax_max")
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """
        - Ensure Locations exist (create by name if missing)
        - Normalize Round Trip pairs textually so (origin, destination) is ordered.
        """
        for col in ("origin", "destination"):
            name = (row.get(col) or "").strip()
            if name:
                Location.objects.get_or_create(name=name)

        if (row.get("trip_type") or "").strip() == "Round Trip":
            a = (row.get("origin") or "").strip()
            b = (row.get("destination") or "").strip()
            if a and b and a > b:
                row["origin"], row["destination"] = b, a

    def before_save_instance(self, instance, using_transactions, dry_run):
        # Final guard to keep A<B for Round Trip rows
        if instance.trip_type == "Round Trip" and instance.origin_id and instance.destination_id:
            if instance.origin_id > instance.destination_id:
                instance.origin_id, instance.destination_id = instance.destination_id, instance.origin_id


# ---------------------------
# Admin registrations
# ---------------------------

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name", "description")
    ordering = ("name",)
    list_per_page = 50


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percentage", "active", "valid_from", "valid_until")
    list_filter = ("active",)
    search_fields = ("code",)
    ordering = ("-active", "-valid_until")
    list_editable = ("active", "discount_percentage")


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "night_charge", "extra_per_passenger_fee")
    list_editable = ("active", "night_charge", "extra_per_passenger_fee")
    search_fields = ("name", "description")
    list_filter = ("active",)
    ordering = ("-active", "name")

    # Optional: keep only one active rule
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.active:
            PricingRule.objects.exclude(pk=obj.pk).update(active=False)


@admin.register(PriceMatrix)
class PriceMatrixAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_classes = [PriceMatrixResource]
    list_display = ("trip_type", "transport_type", "origin", "destination", "pax_min", "pax_max", "price")
    list_filter = (
        "trip_type", "transport_type",
        ("origin", admin.RelatedOnlyFieldListFilter),
        ("destination", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("origin__name", "destination__name")
    ordering = ("origin__name", "destination__name", "trip_type", "transport_type", "pax_min")
    list_editable = ("price",)
    list_per_page = 100
    autocomplete_fields = ("origin", "destination")


class TripLegInline(admin.TabularInline):
    model = TripLeg
    extra = 0
    fields = ("sequence", "pickup_location", "dropoff_location", "pickup_address", "dropoff_address")
    autocomplete_fields = ("pickup_location", "dropoff_location")
    ordering = ("sequence",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = [TripLegInline]

    list_display = (
        "id", "created_at",
        "first_name", "last_name",
        "trip_type", "transport_type",
        "pickup_location", "dropoff_location",
        "passenger_count",
        "price",
        "email", "phone",
    )
    list_filter = (
        "trip_type", "transport_type",
        ("pickup_location", admin.RelatedOnlyFieldListFilter),
        ("dropoff_location", admin.RelatedOnlyFieldListFilter),
        "created_at",
    )
    search_fields = (
        "first_name", "last_name",
        "email", "phone",
        "notes", "flight_number",
        "pickup_address", "dropoff_address",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "price")
    autocomplete_fields = ("pickup_location", "dropoff_location")

    fieldsets = (
        ("Trip Overview", {
            "fields": (
                ("trip_type", "transport_type"),
                ("pickup_location", "dropoff_location"),
                ("pickup_time", "return_time"),
                "summary_leg_preview",
            )
        }),
        ("Addresses (Outbound summary on Booking)", {
            "fields": ("pickup_address", "dropoff_address")
        }),
        ("Passenger & Extras", {
            "fields": (
                ("adults", "children", "luggage"),
                ("booster_seats", "flight_number"),
                ("checkin_date", "checkout_date"),
            )
        }),
        ("Customer", {
            "fields": (
                ("first_name", "last_name"),
                ("email", "country_code", "phone"),
            )
        }),
        ("Pricing & Meta", {
            "fields": ("promo_code", "notes", "price", "created_at")
        }),
    )

    def passenger_count(self, obj):
        return (obj.adults or 0) + (obj.children or 0)
    passenger_count.short_description = "Passengers"

    def summary_leg_preview(self, obj):
        return format_html(
            "<div><b>Leg 1:</b> {} → {}<br>"
            "<small>{} → {}</small></div>",
            obj.pickup_location, obj.dropoff_location,
            (obj.pickup_address or "—"), (obj.dropoff_address or "—"),
        )
    summary_leg_preview.short_description = "Summary (Outbound)"
