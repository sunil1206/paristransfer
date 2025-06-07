from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image


class OptimizedImageMixin:
    """Mixin to optimize and convert images before saving."""
    max_size = (1920, 1080)  # Maximum dimensions
    quality = 80  # Compression quality
    format = "WEBP"  # Output format

    def optimize_image(self, image_field):
        try:
            img = Image.open(image_field)
            img = img.convert("RGB")
            img.thumbnail(self.max_size, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format=self.format, quality=self.quality)
            output.seek(0)

            # Ensure the filename has .webp extension
            filename = f"{image_field.name.rsplit('.', 1)[0]}.webp"
            image_field.save(filename, ContentFile(output.read()), save=False)

        except Exception as e:
            print(f"Error optimizing image: {e}")


class OptimizedImageField(models.ImageField):
    """Custom ImageField to automatically convert images to WebP"""

    def save(self, name, content, save=True):
        img = Image.open(content)
        img = img.convert("RGB")

        output = BytesIO()
        img.save(output, format="WEBP", quality=80)
        output.seek(0)

        # Change file extension to .webp
        name = f"{name.rsplit('.', 1)[0]}.webp"
        content = ContentFile(output.read())

        super().save(name, content, save)


class Service(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    image = OptimizedImageField(upload_to='service/', blank=True, null=True)


    def __str__(self):
        return self.title


class Slider(models.Model, OptimizedImageMixin):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    image = models.ImageField(upload_to='slider_images/')
    rating = models.IntegerField(default=5)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            self.optimize_image(self.image)
        super().save(*args, **kwargs)


class About(models.Model, OptimizedImageMixin):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    description1 = models.TextField()
    description2 = models.TextField()
    phone_number = models.CharField(max_length=20)
    image1 = models.ImageField(upload_to='about_images/')
    image2 = models.ImageField(upload_to='about_images/')
    alt_image1 = models.CharField(max_length=255, blank=True, null=True)
    alt_image2 = models.CharField(max_length=255, blank=True, null=True)
    rating = models.IntegerField(default=5)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image1:
            self.optimize_image(self.image1)
        if self.image2:
            self.optimize_image(self.image2)
        super().save(*args, **kwargs)


class Amenity(models.Model):
    name = models.CharField(max_length=100)
    cab_type = models.CharField(max_length=100)
    icon = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Cab(models.Model, OptimizedImageMixin):
    name = models.CharField(max_length=255)
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='cab_images/')
    description = models.TextField()
    capacity = models.CharField(max_length=50)
    cab_type = models.CharField(max_length=100)
    amenities = models.ManyToManyField(Amenity, related_name='cabs')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image:
            self.optimize_image(self.image)
        super().save(*args, **kwargs)


class Facility(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name


from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question

class Blog(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    date = models.DateField()
    image = models.ImageField(upload_to='blog_images/')
    content = models.TextField()
    slug = models.SlugField(unique=True, blank=True, null=True) #added slug field

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
      #Added slug creation if one does not exist.
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self): #added get_absolute_url
        from django.urls import reverse
        return reverse('blog_post', kwargs={'slug': self.slug})



