from django.contrib import admin
from .models import Equipment, MaintenanceLog


class MaintenanceLogInline(admin.TabularInline):
    model = MaintenanceLog
    extra = 0


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "equipment_type", "status", "location", "next_maintenance_date")
    list_filter = ("status",)
    search_fields = ("name", "equipment_type", "serial_number")
    inlines = [MaintenanceLogInline]


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ("equipment", "log_date", "status_after", "performed_by")
    list_filter = ("status_after",)
