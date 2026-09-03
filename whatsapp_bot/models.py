from django.conf import settings
from django.db import models


class WhatsAppContact(models.Model):
    """A patient/prospect who has messaged the business WhatsApp number."""

    STATE_NEW = "new"
    STATE_MENU = "menu"
    STATE_AWAITING_TEST_QUERY = "awaiting_test_query"
    STATE_AWAITING_AVAILABILITY_QUERY = "awaiting_availability_query"
    STATE_BOOKING_SELECT_TEST = "booking_select_test"
    STATE_BOOKING_SELECT_DATE = "booking_select_date"
    STATE_BOOKING_CONFIRM = "booking_confirm"
    STATE_NEEDS_HUMAN = "needs_human"

    STATE_CHOICES = [
        (STATE_NEW, "New"),
        (STATE_MENU, "At Main Menu"),
        (STATE_AWAITING_TEST_QUERY, "Awaiting Test Name"),
        (STATE_AWAITING_AVAILABILITY_QUERY, "Awaiting Availability Query"),
        (STATE_BOOKING_SELECT_TEST, "Booking: Choosing Test"),
        (STATE_BOOKING_SELECT_DATE, "Booking: Choosing Date"),
        (STATE_BOOKING_CONFIRM, "Booking: Awaiting Confirmation"),
        (STATE_NEEDS_HUMAN, "Needs Human Follow-up"),
    ]

    wa_id = models.CharField("WhatsApp ID / Phone", max_length=32, unique=True)
    profile_name = models.CharField(max_length=150, blank=True)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=STATE_NEW)
    needs_human = models.BooleanField(default=False)
    STATUS_OPEN = "open"
    STATUS_PENDING = "pending"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_PENDING, "Pending"),
        (STATUS_RESOLVED, "Resolved"),
    ]
    conversation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    unread_count = models.PositiveIntegerField(default=0)
    linked_patient = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="whatsapp_contacts"
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_whatsapp_contacts",
        limit_choices_to={"staff_profile__role__in": ["sales_agent", "sales_manager", "manager", "admin"]},
    )

    # Scratch space used while walking through the multi-step appointment booking flow
    pending_product = models.ForeignKey(
        "inventory.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    pending_date_text = models.CharField(max_length=100, blank=True)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.profile_name or 'Unknown'} ({self.wa_id})"


class WhatsAppMessageLog(models.Model):
    DIRECTION_IN = "in"
    DIRECTION_OUT = "out"
    DIRECTION_CHOICES = [(DIRECTION_IN, "Incoming"), (DIRECTION_OUT, "Outgoing (bot)")]

    contact = models.ForeignKey(WhatsAppContact, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES)
    body = models.TextField()
    wa_message_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.get_direction_display()}] {self.contact.wa_id}: {self.body[:40]}"


class Appointment(models.Model):
    """A test/scan appointment requested through the WhatsApp bot."""

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Staff Confirmation"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    contact = models.ForeignKey(WhatsAppContact, on_delete=models.CASCADE, related_name="appointments")
    product = models.ForeignKey("inventory.Product", on_delete=models.SET_NULL, null=True, related_name="+")
    preferred_date_text = models.CharField(max_length=100, help_text="Free-text date/time the patient asked for")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        test_name = self.product.name if self.product else "Unspecified test"
        return f"{test_name} for {self.contact} ({self.preferred_date_text})"
