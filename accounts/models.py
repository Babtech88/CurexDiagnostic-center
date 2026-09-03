from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_CASHIER = "cashier"
    ROLE_SALES_MANAGER = "sales_manager"
    ROLE_SALES_AGENT = "sales_agent"
    ROLE_LAB_TECH = "lab_tech"
    ROLE_DELIVERY = "delivery"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_MANAGER, "Lab Manager"),
        (ROLE_CASHIER, "Front Desk / Receptionist"),
        (ROLE_SALES_MANAGER, "Sales Manager"),
        (ROLE_SALES_AGENT, "Sales Agent"),
        (ROLE_LAB_TECH, "Lab Technician / Phlebotomist"),
        (ROLE_DELIVERY, "Sample Collection Rider"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CASHIER)
    phone_number = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active_staff = models.BooleanField(default=True)
    photo = models.ImageField(upload_to="staff_photos/", blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Opt-in fields for the public "Our Specialists" section — nothing shows publicly unless
    # a real staff member (or admin, with their consent) explicitly enables this.
    show_on_website = models.BooleanField(
        default=False, help_text="Show this staff member on the public 'Our Specialists' section"
    )
    public_title = models.CharField(
        max_length=150, blank=True, help_text="e.g. 'Consultant Pathologist' — shown publicly instead of the internal role"
    )
    public_bio = models.TextField(blank=True, help_text="Short public bio/qualifications shown on the website")

    class Meta:
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager_or_admin(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_MANAGER, self.ROLE_SALES_MANAGER)

    @property
    def is_sales_manager_or_admin(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_MANAGER, self.ROLE_SALES_MANAGER)

    @property
    def is_sales_agent(self):
        return self.role == self.ROLE_SALES_AGENT
