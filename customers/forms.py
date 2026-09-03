from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone_number", "email", "address", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
