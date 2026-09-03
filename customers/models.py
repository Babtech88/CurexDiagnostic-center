from django.db import models


class Customer(models.Model):
    """A patient record — used for bookings, results history, and contact info."""

    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    @property
    def total_spent(self):
        total = 0
        for sale in self.sales.all():
            total += sale.total_amount
        return total

    @property
    def order_count(self):
        return self.sales.count()
