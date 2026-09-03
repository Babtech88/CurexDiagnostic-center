from django.contrib import admin
from .models import WhatsAppOrder, WhatsAppOrderItem, DeliveryRequest


class WhatsAppOrderItemInline(admin.TabularInline):
    model = WhatsAppOrderItem
    extra = 1


@admin.register(WhatsAppOrder)
class WhatsAppOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_phone", "status", "wants_delivery", "created_at")
    list_filter = ("status", "wants_delivery")
    inlines = [WhatsAppOrderItemInline]


@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient_name", "phone_number", "status", "assigned_rider", "scheduled_date")
    list_filter = ("status",)
