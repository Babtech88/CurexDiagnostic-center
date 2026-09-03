from django.conf import settings
from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    STATUS_OPERATIONAL = "operational"
    STATUS_NEEDS_MAINTENANCE = "needs_maintenance"
    STATUS_UNDER_REPAIR = "under_repair"
    STATUS_OFFLINE = "offline"

    STATUS_CHOICES = [
        (STATUS_OPERATIONAL, "Operational"),
        (STATUS_NEEDS_MAINTENANCE, "Needs Maintenance"),
        (STATUS_UNDER_REPAIR, "Under Repair"),
        (STATUS_OFFLINE, "Offline"),
    ]

    name = models.CharField(max_length=150)
    equipment_type = models.CharField(max_length=150, blank=True, help_text="e.g. Haematology Analyzer, Ultrasound Scanner")
    photo = models.ImageField(upload_to="equipment_photos/", blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, help_text="e.g. Lab Room 1, Scan Room")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPERATIONAL)
    serial_number = models.CharField(max_length=100, blank=True)
    last_serviced_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment_assigned"
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Equipment"

    def __str__(self):
        return self.name

    @property
    def is_overdue_for_maintenance(self):
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date < timezone.localdate()

    @property
    def is_maintenance_due_soon(self):
        if not self.next_maintenance_date:
            return False
        days_left = (self.next_maintenance_date - timezone.localdate()).days
        return 0 <= days_left <= 14


class MaintenanceLog(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="maintenance_logs")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    log_date = models.DateField(default=timezone.localdate)
    description = models.TextField()
    status_after = models.CharField(max_length=20, choices=Equipment.STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-log_date", "-created_at"]

    def __str__(self):
        return f"{self.equipment.name} - {self.log_date}"
