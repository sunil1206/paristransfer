import numpy as np
from django.shortcuts import render, get_object_or_404

# Create your views here.
from booking.views import load_model, get_float_value
from core.models import Slider, About, Cab, Amenity, Service, FAQ, Blog
from seo.models import SEOSettings

def handling_404(request, exception):
    return render(request, 'core/404.html', {})

def index(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='Home')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings

    slider_items = Slider.objects.filter(is_active=True).order_by('order')
    about = About.objects.first()
    cabs = Cab.objects.prefetch_related('amenities').all()
    amenity = Amenity.objects.all()
    services = Service.objects.all()
    faqs = FAQ.objects.all()
    # blog_posts = Blog.objects.all()
    blogs = Blog.objects.order_by('-date')  # Newest first

    # Prediction logic
    predicted_price = None
    if request.method == "POST":
        try:
            print("Received POST request with data:", request.POST)  # Debugging

            # Extract features from the form
            features = np.array([[
                get_float_value(request, "trip_type"),
                get_float_value(request, "pickup_location"),
                get_float_value(request, "dropoff_location"),
                get_float_value(request, "transport_type"),
                get_float_value(request, "adults"),
                get_float_value(request, "children"),
                get_float_value(request, "luggage"),
                get_float_value(request, "pickup_time"),
                get_float_value(request, "return_time"),
            ]])

            # Load the trained model
            price_model = load_model('booking/models/taxi_price_classifier.joblib')

            print("Predicting with features:", features)  # Debugging
            predicted_price = round(price_model.predict(features)[0])

        except Exception as e:
            print(f"Error occurred: {e}")  # Debugging
            predicted_price = f"Error: {e}"

    context = {
        'canonical_url': canonical_url,
        'seo_settings': seo_settings,
        'slider_items': slider_items,
        'about': about,
        'cabs': cabs,
        'amenity': amenity,
        'services': services,
        'faqs': faqs,
        # 'blog_posts': blog_posts,
        'predicted_price': predicted_price,  # Add predicted price to context
        'blogs':blogs,
    }
    return render(request, 'core/index.html', context)



def about(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='About Us')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings
    about = About.objects.first()
    faqs = FAQ.objects.all()
    context = {'canonical_url': canonical_url,
               'seo_settings': seo_settings,
               'about':about,
               'faqs':faqs
               }
    return render(request, 'url/aboutpage.html',context)

def service(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='Service')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings
    context = {'canonical_url': canonical_url,
               'seo_settings': seo_settings
               }
    return render(request, 'url/servicepage.html', context)

# def contact(request):
#     canonical_url = request.build_absolute_uri()
#     try:
#         seo_settings = SEOSettings.objects.get(title='Contact')
#     except SEOSettings.DoesNotExist:
#         seo_settings = None  # Or provide default SEO settings
#     context = {'canonical_url': canonical_url,
#                'seo_settings': seo_settings
#                }
#     return render(request, 'core/contactpage.html', context)


def blog_post(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    return render(request, 'blog/blogdetail.html', {'blog': blog})