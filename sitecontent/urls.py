from django.urls import path
from . import views

app_name = "sitecontent"

urlpatterns = [
    path("newsletter/", views.newsletter_signup, name="newsletter_signup"),

    path("testimonials/", views.testimonial_list, name="testimonial_list"),
    path("testimonials/add/", views.testimonial_create, name="testimonial_create"),
    path("testimonials/<int:pk>/edit/", views.testimonial_edit, name="testimonial_edit"),
    path("testimonials/<int:pk>/delete/", views.testimonial_delete, name="testimonial_delete"),

    path("articles/", views.article_list, name="article_list"),
    path("articles/add/", views.article_create, name="article_create"),
    path("articles/<int:pk>/edit/", views.article_edit, name="article_edit"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),

    path("staff-profiles/", views.staff_public_profiles, name="staff_public_profiles"),
    path("staff-profiles/<int:pk>/edit/", views.staff_public_edit, name="staff_public_edit"),
]
