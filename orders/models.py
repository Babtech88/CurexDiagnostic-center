from django.conf import settings
from django.db import models
from urllib.parse import quote


class WhatsAppOrder(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_FULFILLED = "fulfilled"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_FULFILLED, "Fulfilled"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    contact = models.ForeignKey(
        "whatsapp_bot.WhatsAppContact", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="whatsapp_orders"
    )
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING)
    payment_reference = models.CharField(max_length=120, blank=True)
    wants_delivery = models.BooleanField(default=False)
    delivery_address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"WhatsApp Order #{self.pk} - {self.customer_name}"

    @property
    def total_amount(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    def build_whatsapp_message(self):
        lines = [f"New test booking request — {settings.SITE_NAME}"]
        lines.append(f"Patient: {self.customer_name} ({self.customer_phone})")
        for item in self.items.all():
            lines.append(f"- {item.quantity} x {item.product.name} (@{item.unit_price} each)")
        lines.append(f"Total: {self.total_amount}")
        if self.wants_delivery:
            lines.append(f"Home sample collection requested at: {self.delivery_address}")
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)

    def whatsapp_link(self):
        message = quote(self.build_whatsapp_message())
        return f"https://wa.me/{settings.WHATSAPP_BUSINESS_NUMBER}?text={message}"


class WhatsAppOrderItem(models.Model):
    order = models.ForeignKey(WhatsAppOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="whatsapp_order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class DeliveryRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_DISPATCHED = "dispatched"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DISPATCHED, "Dispatched"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    whatsapp_order = models.ForeignKey(
        WhatsAppOrder, on_delete=models.CASCADE, null=True, blank=True, related_name="delivery_requests"
    )
    sale = models.ForeignKey(
        "sales.Sale", on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_requests"
    )
    recipient_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING)
    payment_reference = models.CharField(max_length=120, blank=True)
    assigned_rider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )
    scheduled_date = models.DateField(null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Delivery to {self.recipient_name} ({self.get_status_display()})"
