from django.urls import path
from . import views

app_name = "articles"

urlpatterns = [
    path("", views.article_public_list, name="list"),
    path("<slug:slug>/", views.article_public_detail, name="detail"),
]
