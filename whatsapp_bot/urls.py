from django.urls import path
from . import views

app_name = "whatsapp_bot"

urlpatterns = [
    path("webhook/", views.webhook, name="webhook"),
    path("status/", views.bot_status, name="status"),
    path("conversations/", views.conversation_list, name="conversation_list"),
    path("conversations/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("conversations/<int:pk>/assign/", views.assign_conversation, name="assign_conversation"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/<int:pk>/status/<str:status>/", views.appointment_set_status, name="appointment_set_status"),
]
