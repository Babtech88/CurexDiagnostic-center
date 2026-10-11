from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

# Avoid visually-ambiguous characters (0/O, 1/I/l) in codes patients have to type on a phone
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_access_code():
    return get_random_string(8, allowed_chars=CODE_ALPHABET)


class TestResult(models.Model):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="test_results"
    )
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    appointment = models.ForeignKey(
        "whatsapp_bot.Appointment", on_delete=models.SET_NULL, null=True, blank=True, related_name="results"
    )
    file = models.FileField(upload_to="results/%Y/%m/", help_text="PDF or image of the result")
    result_summary = models.CharField(
        max_length=200, blank=True, help_text="Optional short note, e.g. 'Normal' or 'See attached report'"
    )
    access_code = models.CharField(max_length=12, unique=True, default=generate_access_code, editable=False)
    is_released = models.BooleanField(
        default=True, help_text="Uncheck to hide this result from the patient portal without deleting it"
    )
    test_date = models.DateField(null=True, blank=True, help_text="Date the sample was collected / test performed")
    notes = models.TextField(blank=True, help_text="Internal notes, not shown to the patient")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    patient_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        test_name = self.product.name if self.product else "Result"
        return f"{test_name} — {self.customer.name} ({self.access_code})"

    def regenerate_access_code(self):
        self.access_code = generate_access_code()
        self.save(update_fields=["access_code"])
