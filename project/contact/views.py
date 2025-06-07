from django.shortcuts import render

from seo.models import SEOSettings
from .models import ContactMessage
from .forms import ContactMessageForm

def contact(request):
    canonical_url = request.build_absolute_uri()
    try:
        seo_settings = SEOSettings.objects.get(title='Contact')
    except SEOSettings.DoesNotExist:
        seo_settings = None  # Or provide default SEO settings
    message = None  # Default message as None

    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()  # Save the message to the database
            message = "Your message was sent successfully."  # Set the success message
            form = ContactMessageForm()  # Reset the form for another submission (optional)
    else:
        form = ContactMessageForm()
    context = {'canonical_url': canonical_url,
               'seo_settings': seo_settings,
               'form': form,
               'message': message
               }

    return render(request, 'url/contactpage.html', context)
