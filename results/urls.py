from django.urls import path
from . import views

app_name = "results"

urlpatterns = [
    # Public
    path("", views.result_lookup, name="lookup"),
    path("view/<int:pk>/<str:access_code>/", views.result_view_print, name="view_print"),

    # Staff
    path("manage/", views.result_list, name="result_list"),
    path("manage/upload/", views.result_upload, name="result_upload"),
    path("manage/<int:pk>/", views.result_detail, name="result_detail"),
    path("manage/<int:pk>/notify/", views.result_notify_patient, name="result_notify"),
]
