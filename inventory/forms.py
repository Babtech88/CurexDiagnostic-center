from django import forms
from .models import Product, Category, Supplier, Promotion


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "supplier", "description", "image",
            "cost_price", "selling_price", "stock_quantity", "low_stock_threshold",
            "expiry_date", "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone_number", "email", "address"]


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ["title", "banner_text", "products", "discount_percent", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "products": forms.CheckboxSelectMultiple,
        }


class RestockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity to add")
    note = forms.CharField(required=False, max_length=255)
