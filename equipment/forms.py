from django import forms
from .models import Equipment, MaintenanceLog


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            "name", "equipment_type", "photo", "location", "status", "serial_number",
            "last_serviced_date", "next_maintenance_date", "assigned_technician", "notes",
        ]
        widgets = {
            "last_serviced_date": forms.DateInput(attrs={"type": "date"}),
            "next_maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class QuickStatusForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["status"]


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ["log_date", "description", "status_after"]
        widgets = {
            "log_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
