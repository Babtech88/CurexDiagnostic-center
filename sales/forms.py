from django import forms
from .models import Sale
from customers.models import Customer


class NewSaleForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    payment_method = forms.ChoiceField(choices=Sale.PAYMENT_CHOICES)
