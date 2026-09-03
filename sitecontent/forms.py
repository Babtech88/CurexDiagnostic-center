from django import forms
from .models import Testimonial, Article
from accounts.models import StaffProfile


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["patient_name", "rating", "quote", "photo", "is_approved"]
        widgets = {"quote": forms.Textarea(attrs={"rows": 3})}


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "category", "cover_image", "excerpt", "body", "is_published", "published_at"]
        widgets = {
            "excerpt": forms.Textarea(attrs={"rows": 2}),
            "body": forms.Textarea(attrs={"rows": 10}),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class StaffPublicProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ["show_on_website", "public_title", "public_bio", "photo"]
