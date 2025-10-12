# admin.py

from django.contrib import admin
from .models import (
    Service,
    Slider,
    About,
    Amenity,
    Cab,
    Facility,
    FAQ,
    Blog,
    Feature,
)

# Using the @admin.register decorator for a clean, modern registration approach.

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin configuration for the Service model."""
    list_display = ('title', 'alt_text')
    search_fields = ('title', 'description')

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    """Admin configuration for the Slider model."""
    list_display = ('title', 'subtitle', 'is_active', 'order', 'rating')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order', 'rating')
    search_fields = ('title', 'subtitle')

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    """Admin configuration for the About model."""
    # Using fieldsets to organize the edit form for better readability
    fieldsets = (
        ('Header Information', {
            'fields': ('title', 'subtitle')
        }),
        ('Detailed Content', {
            'fields': ('description1', 'description2', 'phone_number', 'rating')
        }),
        ('Images', {
            'fields': ('image1', 'alt_image1', 'image2', 'alt_image2')
        }),
    )

    def has_add_permission(self, request):
        # This prevents adding more than one 'About' instance (Singleton pattern)
        return not About.objects.exists()

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """Admin configuration for the Amenity model."""
    list_display = ('name', 'cab_type')
    list_filter = ('cab_type',)
    search_fields = ('name',)

@admin.register(Cab)
class CabAdmin(admin.ModelAdmin):
    """Admin configuration for the Cab model."""
    list_display = ('name', 'cab_type', 'price_per_km', 'capacity')
    list_filter = ('cab_type', 'amenities')
    search_fields = ('name', 'description')
    # filter_horizontal provides a much better UI for ManyToManyFields
    filter_horizontal = ('amenities',)

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Admin configuration for the Facility model."""
    list_display = ('name', 'icon')
    search_fields = ('name', 'description')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for the FAQ model."""
    list_display = ('question',)
    search_fields = ('question', 'answer')

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """Admin configuration for the Blog model."""
    list_display = ('title', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title', 'content')
    # Automatically generates the slug from the title field
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Admin configuration for the Feature model."""
    list_display = ('name', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'description')