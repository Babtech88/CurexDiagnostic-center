from django.contrib import admin
from .models import WhatsAppContact, WhatsAppMessageLog, Appointment


class WhatsAppMessageLogInline(admin.TabularInline):
    model = WhatsAppMessageLog
    extra = 0
    readonly_fields = ("direction", "body", "wa_message_id", "created_at")
    can_delete = False


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ("wa_id", "profile_name", "state", "needs_human", "last_seen")
    list_filter = ("state", "needs_human")
    search_fields = ("wa_id", "profile_name")
    inlines = [WhatsAppMessageLogInline]


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = ("contact", "direction", "body", "created_at")
    list_filter = ("direction",)
    search_fields = ("contact__wa_id", "body")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("contact", "product", "preferred_date_text", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("contact__wa_id", "contact__profile_name", "product__name")
