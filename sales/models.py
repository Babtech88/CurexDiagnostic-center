from django.conf import settings
from django.db import models


class Sale(models.Model):
    PAYMENT_CASH = "cash"
    PAYMENT_TRANSFER = "transfer"
    PAYMENT_CARD = "card"
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_TRANSFER, "Bank Transfer"),
        (PAYMENT_CARD, "Card"),
    ]

    SOURCE_IN_STORE = "in_store"
    SOURCE_WHATSAPP = "whatsapp"
    SOURCE_CHOICES = [
        (SOURCE_IN_STORE, "In-store"),
        (SOURCE_WHATSAPP, "WhatsApp Order"),
    ]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_IN_STORE)
    whatsapp_order = models.ForeignKey(
        "orders.WhatsAppOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="resulting_sales"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sale #{self.pk} - {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def total_amount(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def total_profit(self):
        return sum((item.profit for item in self.items.all()), start=0)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at time of sale")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cost at time of sale")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    @property
    def profit(self):
        return (self.unit_price - self.unit_cost) * self.quantity
