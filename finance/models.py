from django.conf import settings
from django.db import models


class Expense(models.Model):
    CATEGORY_RENT = "rent"
    CATEGORY_UTILITIES = "utilities"
    CATEGORY_SALARIES = "salaries"
    CATEGORY_SUPPLIES = "supplies"
    CATEGORY_MAINTENANCE = "maintenance"
    CATEGORY_MARKETING = "marketing"
    CATEGORY_TRANSPORT = "transport"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_RENT, "Rent"),
        (CATEGORY_UTILITIES, "Utilities (power, water, internet)"),
        (CATEGORY_SALARIES, "Salaries & Wages"),
        (CATEGORY_SUPPLIES, "Reagents & Supplies"),
        (CATEGORY_MAINTENANCE, "Equipment Maintenance"),
        (CATEGORY_MARKETING, "Marketing"),
        (CATEGORY_TRANSPORT, "Transport / Logistics"),
        (CATEGORY_OTHER, "Other"),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    receipt = models.FileField(upload_to="expense_receipts/%Y/%m/", blank=True, null=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.description} (\u20a6{self.amount:,.0f})"
