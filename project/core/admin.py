from django.contrib import admin
from .models import Slider, Service, FAQ
from django.utils.html import format_html

class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'rating', 'is_active', 'order')
    list_editable = ('rating', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'image', 'alt_text', 'link')
        }),
        ('Advanced Options', {
            'classes': ('collapse',),
            'fields': ('rating', 'is_active', 'order'),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "No Image"

    image_preview.short_description = 'Image Preview'


admin.site.register(Slider, SliderAdmin)


from django.contrib import admin
from .models import About
from django.utils.html import format_html

class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'image1_preview', 'image2_preview', 'rating')
    list_editable = ('rating',)
    search_fields = ('title', 'subtitle', 'description1', 'description2')
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'description1', 'description2', 'phone_number', 'rating')
        }),
        ('Images', {
            'fields': ('image1', 'alt_image1', 'image2', 'alt_image2'),
        }),
    )

    def image1_preview(self, obj):
        if obj.image1:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image1.url)
        return "No Image"
    image1_preview.short_description = 'Image 1 Preview'

    def image2_preview(self, obj):
        if obj.image2:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image2.url)
        return "No Image"
    image2_preview.short_description = 'Image 2 Preview'

admin.site.register(About, AboutAdmin)


from .models import Amenity, Cab


class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'cab_type')
    list_filter = ('cab_type',)
    search_fields = ('name', 'cab_type')

admin.site.register(Amenity, AmenityAdmin)

class AmenityInline(admin.TabularInline):
    model = Cab.amenities.through
    extra = 1

class CabAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_km', 'capacity', 'cab_type', 'image_preview')
    list_filter = ('cab_type', 'capacity')
    search_fields = ('name', 'description', 'cab_type', 'capacity')
    inlines = [AmenityInline]
    exclude = ('amenities',)  # Exclude the ManyToManyField from the main form
    fieldsets = (
        (None, {
            'fields': ('name', 'price_per_km', 'description', 'capacity', 'cab_type', 'image')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "No Image"

    image_preview.short_description = 'Image Preview'

admin.site.register(Cab, CabAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'image_preview', 'alt_text')
    list_filter = ('title', 'alt_text')  # Adjust based on relevant fields you want to filter by
    search_fields = ('title', 'description', 'alt_text')  # Fields for searching
    # exclude = ('alt_text',)  # You can exclude the alt_text if you don't want it to appear in the main form
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image', 'alt_text')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "No Image"

    image_preview.short_description = 'Image Preview'

admin.site.register(Service, ServiceAdmin)
admin.site.register(FAQ)

from django.contrib import admin
from .models import Blog

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date')
    search_fields = ('title', 'category')
    prepopulated_fields = {'slug': ('title',)} #added prepopulated slug
    date_hierarchy = 'date'



