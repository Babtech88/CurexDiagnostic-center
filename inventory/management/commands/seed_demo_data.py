import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import StaffProfile
from customers.models import Customer
from inventory.models import Category, Supplier, Product, Promotion

REAGENTS_AND_CONSUMABLES = [
    # name, category, cost, price, stock, expiry_days_from_today (None = no expiry)
    ("Malaria RDT Kit (box of 25)", "Reagents & Kits", 8000, 12000, 3, 20),
    ("HIV Rapid Test Kit (box of 30)", "Reagents & Kits", 15000, 22000, 2, 10),
    ("Glucose Test Strips (box)", "Reagents & Kits", 4500, 7000, 15, 200),
    ("Widal Antigen Reagent Set", "Reagents & Kits", 9000, 13500, 4, 5),
    ("VDRL Antigen Reagent Set", "Reagents & Kits", 7000, 10500, 3, 15),
    ("Blood Collection Tubes (EDTA, pack)", "Consumables", 3000, 4500, 40, 400),
    ("Disposable Syringes (box of 100)", "Consumables", 2500, 3800, 6, None),
    ("Lab Gloves (box, medium)", "Consumables", 2000, 3200, 25, None),
    ("Specimen Containers (pack of 50)", "Consumables", 3500, 5000, 8, None),
]


class Command(BaseCommand):
    help = (
        "Seed the database with Curex Diagnostic Center data: staff, the official price list, "
        "reagents/consumables, a promotion, category images, and demo patients."
    )

    def handle(self, *args, **options):
        today = timezone.localdate()

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", "curex.diagcenter@gmail.com", "admin12345")
            StaffProfile.objects.create(user=admin, role=StaffProfile.ROLE_ADMIN, phone_number="09122997406")
            self.stdout.write(self.style.SUCCESS("Created admin user (username=admin, password=admin12345)"))

        if not User.objects.filter(username="labtech").exists():
            labtech = User.objects.create_user("labtech", "labtech@example.com", "labtech12345", first_name="Chidinma")
            StaffProfile.objects.create(user=labtech, role=StaffProfile.ROLE_LAB_TECH, phone_number="2348010000002")
            self.stdout.write(self.style.SUCCESS("Created lab tech user (username=labtech, password=labtech12345)"))

        if not User.objects.filter(username="frontdesk").exists():
            frontdesk = User.objects.create_user("frontdesk", "frontdesk@example.com", "frontdesk12345", first_name="Bashir")
            StaffProfile.objects.create(user=frontdesk, role=StaffProfile.ROLE_CASHIER, phone_number="2348010000003")
            self.stdout.write(self.style.SUCCESS("Created front desk user (username=frontdesk, password=frontdesk12345)"))

        # --- Official price list (the real Curex catalog — see load_official_price_list.py) ---
        call_command("load_official_price_list")

        # --- Reagents & consumables — trackable internal stock with expiry ---
        supplier, _ = Supplier.objects.get_or_create(
            name="MedLab Supplies Nigeria", defaults={"phone_number": "2348012223344", "email": "orders@medlabsupplies.ng"}
        )
        sku_counter = 1
        for name, cat, cost, price, stock, expiry_days in REAGENTS_AND_CONSUMABLES:
            expiry = today + timedelta(days=expiry_days) if expiry_days else None
            category, _ = Category.objects.get_or_create(name=cat)
            Product.objects.get_or_create(
                sku=f"SUP-{sku_counter:04d}",
                defaults=dict(
                    name=name, category=category, supplier=supplier,
                    cost_price=cost, selling_price=price, stock_quantity=stock,
                    low_stock_threshold=5, expiry_date=expiry,
                ),
            )
            sku_counter += 1
        self.stdout.write(self.style.SUCCESS("Seeded reagents & consumables."))

        # --- Category illustrations for every test ---
        call_command("assign_test_images")

        # --- A sample promotion on real Haematology tests ---
        promo, created = Promotion.objects.get_or_create(
            title="Health Awareness Week",
            defaults=dict(
                banner_text="Discounted screening tests all week - walk in or book on WhatsApp!",
                discount_percent=20,
                start_date=today,
                end_date=today + timedelta(days=7),
                is_active=True,
            ),
        )
        if created:
            haem_tests = list(Product.objects.filter(
                is_active=True, category__name="Haematology & Blood Group Serology"
            ))
            promo.products.set(random.sample(haem_tests, min(4, len(haem_tests))))
            self.stdout.write(self.style.SUCCESS("Created 'Health Awareness Week' promotion."))

        # --- Demo patients ---
        demo_patients = [
            ("Tolu Adeyemi", "2348030000001", "tolu@example.com"),
            ("Ifeoma Okafor", "2348030000002", "ifeoma@example.com"),
            ("Bashir Mohammed", "2348030000003", ""),
        ]
        for name, phone, email in demo_patients:
            Customer.objects.get_or_create(phone_number=phone, defaults={"name": name, "email": email})
        self.stdout.write(self.style.SUCCESS("Seeded demo patients."))

        self.stdout.write(self.style.SUCCESS("\nDone! Log in at /accounts/login/ with admin / admin12345"))
