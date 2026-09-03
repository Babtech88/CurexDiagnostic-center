from django.db import models
from django.utils.text import slugify


class Testimonial(models.Model):
    """A real patient testimonial, added manually by staff. Never auto-generated."""

    patient_name = models.CharField(max_length=150)
    rating = models.PositiveSmallIntegerField(default=5, help_text="1-5 stars")
    quote = models.TextField()
    photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    is_approved = models.BooleanField(default=False, help_text="Only approved testimonials show on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_name} ({self.rating}\u2605)"


class Article(models.Model):
    """A real health/blog article, written and published by staff."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    cover_image = models.ImageField(upload_to="articles/", blank=True, null=True)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email
