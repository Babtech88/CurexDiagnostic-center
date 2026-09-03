from django import forms
from .models import DeliveryRequest


class WhatsAppOrderStartForm(forms.Form):
    customer_name = forms.CharField(max_length=150, label="Patient Name")
    customer_phone = forms.CharField(max_length=20, label="Phone Number")
    wants_delivery = forms.BooleanField(required=False, label="Request home sample collection")
    delivery_address = forms.CharField(max_length=255, required=False, label="Collection Address")
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)


class DeliveryStatusForm(forms.ModelForm):
    class Meta:
        model = DeliveryRequest
        fields = ["status", "assigned_rider", "scheduled_date", "delivery_fee", "notes"]
        widgets = {"scheduled_date": forms.DateInput(attrs={"type": "date"})}
