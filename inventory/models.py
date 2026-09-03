from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """A billable diagnostic test/service, or a trackable lab consumable/reagent/kit."""

    name = models.CharField(max_length=200, help_text="e.g. 'Full Blood Count', 'Abdominal Ultrasound', or 'Malaria RDT Kit'")
    sku = models.CharField("Test/Item Code", max_length=64, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    description = models.TextField(blank=True, help_text="Test details, sample type required, turnaround time, etc.")
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price charged to the patient")

    stock_quantity = models.PositiveIntegerField(default=0, help_text="For tests: available test slots/kits. For reagents: units in stock.")
    low_stock_threshold = models.PositiveIntegerField(default=5)

    expiry_date = models.DateField(null=True, blank=True, help_text="Reagent/kit expiry date. Leave blank for services with no physical expiry.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse("inventory:product_detail", args=[self.pk])

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    @property
    def is_expired(self):
        return bool(self.expiry_date) and self.expiry_date < timezone.localdate()

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        days_left = (self.expiry_date - timezone.localdate()).days
        return 0 <= days_left <= settings.EXPIRY_WARNING_DAYS

    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.localdate()).days

    @property
    def active_promotion(self):
        today = timezone.localdate()
        return self.promotions.filter(is_active=True, start_date__lte=today, end_date__gte=today).first()

    @property
    def current_price(self):
        promo = self.active_promotion
        if promo:
            return promo.discounted_price(self.selling_price)
        return self.selling_price


def default_promotion_end_date():
    return timezone.localdate() + timedelta(days=7)


class Promotion(models.Model):
    """An advertised sale/discount, tied to one or more products."""

    title = models.CharField(max_length=150)
    banner_text = models.CharField(max_length=255, blank=True, help_text="Short text shown on storefront banner")
    products = models.ManyToManyField(Product, related_name="promotions")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g. 15.00 for 15% off")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(default=default_promotion_end_date)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} (-{self.discount_percent}%)"

    def discounted_price(self, price):
        from decimal import Decimal

        discount = (Decimal(self.discount_percent) / Decimal(100)) * Decimal(price)
        return (Decimal(price) - discount).quantize(Decimal("0.01"))

    @property
    def is_currently_running(self):
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date


class StockMovement(models.Model):
    """Audit trail for stock changes (restock, sale deduction, correction)."""

    REASON_RESTOCK = "restock"
    REASON_SALE = "sale"
    REASON_CORRECTION = "correction"
    REASON_EXPIRED_REMOVAL = "expired_removal"

    REASON_CHOICES = [
        (REASON_RESTOCK, "Restock"),
        (REASON_SALE, "Sale"),
        (REASON_CORRECTION, "Manual Correction"),
        (REASON_EXPIRED_REMOVAL, "Expired Stock Removed"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_movements")
    quantity_change = models.IntegerField(help_text="Positive for additions, negative for deductions")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name}: {self.quantity_change:+d} ({self.reason})"
