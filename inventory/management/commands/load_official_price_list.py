"""
Loads/updates the official Curex Diagnostic Center price list (as provided by the client)
into the database. Safe to re-run any time prices change — matches by test name and updates
the price rather than duplicating entries.

Any previously-seeded billable test that is NOT part of this official list gets deactivated
(is_active=False) rather than deleted, so historical sales/results referencing it stay intact.
Reagents/Kits and Consumables (internal stock, not part of this price list) are left untouched.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Category, Product

# (category_name, [(sku_suffix, test_name, price), ...])
OFFICIAL_PRICE_LIST = {
    "Clinical Chemistry": [
        ("CC001", "Kidney Function Test / Full Electrolytes (Panel)", 8500),
        ("CC002", "Sodium", 2500),
        ("CC003", "Potassium", 2500),
        ("CC004", "Chloride", 2500),
        ("CC005", "Bicarbonate", 2500),
        ("CC006", "Urea", 2500),
        ("CC007", "Creatinine", 2500),
        ("CC008", "Liver Function Test (Panel)", 10000),
        ("CC009", "Total Bilirubin", 3000),
        ("CC010", "Direct Bilirubin", 3000),
        ("CC011", "Alkaline Phosphatase", 3000),
        ("CC012", "S.G.O.T. (AST)", 3000),
        ("CC013", "S.G.P.T. (ALT)", 3000),
        ("CC014", "Total Protein", 4000),
        ("CC015", "Albumin", 2500),
        ("CC016", "Globulin", 2500),
        ("CC017", "Protein Electrophoresis", 12000),
        ("CC018", "Acid Phosphatase", 6000),
        ("CC019", "Full Lipid Profile (Panel)", 10000),
        ("CC020", "HDL Cholesterol (only)", 3000),
        ("CC021", "LDL Cholesterol (only)", 3000),
        ("CC022", "Cholesterol (only)", 3000),
        ("CC023", "Triglyceride (only)", 3000),
        ("CC024", "Fasting Blood Sugar", 1500),
        ("CC025", "Random Blood Sugar", 1500),
        ("CC026", "2hrs Post Prandial Blood Sugar", 3000),
        ("CC027", "Glucose Tolerance Test (GTT)", 10000),
        ("CC028", "Uric Acid", 4000),
        ("CC029", "Calcium", 4500),
        ("CC030", "Phosphate", 6000),
        ("CC031", "Amylase", 5000),
        ("CC032", "Iron", 5000),
        ("CC033", "Magnesium", 5000),
        ("CC034", "Lithium Level", 5000),
        ("CC035", "Creatine Phosphokinase (CPK)", 6000),
        ("CC036", "Complete Urinalysis", 1000),
        ("CC037", "Heaf's / Mantoux Test", 3000),
        ("CC038", "Chlamydia Test", 5000),
    ],
    "Haematology & Blood Group Serology": [
        ("HM001", "Full Blood Count (FBC)", 3500),
        ("HM002", "Haemoglobin (HB)", 1000),
        ("HM003", "Packed Cell Volume (PCV)", 1000),
        ("HM004", "White Cell Count (WCC)", 1000),
        ("HM005", "Glycosylated Haemoglobin (HbA1c)", 10000),
        ("HM006", "Blood Film", 1000),
        ("HM007", "Differential White Cell Count", 1000),
        ("HM008", "Mean Corpuscular Hb Concentration (MCHC)", 1000),
        ("HM009", "Mean Cell Volume (MCV)", 1000),
        ("HM010", "Mean Corpuscular Haemoglobin (MCH)", 1000),
        ("HM011", "Red Cell Count (RCC)", 2000),
        ("HM012", "Sickle Cell Screening", 2500),
        ("HM013", "HB Genotype", 2500),
        ("HM014", "Reticulocyte Count", 2000),
    ],
    "Microbiology": [
        ("MB001", "Culture & Sensitivity", 3000),
        ("MB002", "HVS M/C/S", 3000),
        ("MB003", "Urine M/C/S", 3000),
        ("MB004", "Wound Swab", 3000),
        ("MB005", "Throat Swab", 3000),
        ("MB006", "Stool M/C/S", 3000),
        ("MB007", "Aspirate M/C/S", 3000),
        ("MB008", "H. Pylori", 4000),
        ("MB009", "Stool Microscopy (R/E)", 2000),
        ("MB010", "Occult Blood", 4000),
        ("MB011", "Blood Culture & Sensitivity", 7000),
        ("MB012", "Widal Reaction", 2000),
        ("MB013", "VDRL", 1000),
        ("MB014", "Rheumatoid Factor", 2500),
        ("MB015", "A.S.O. Titre", 3000),
        ("MB016", "Hepatitis B", 2000),
        ("MB017", "Sputum ZN for AAFB x3", 4000),
        ("MB018", "CSF Microscopy & Cell Count", 3000),
    ],
    "Scan": [
        ("SC001", "Obstetrics Scan", 2000),
        ("SC002", "Pelvic Scan", 2000),
        ("SC003", "Lower Abdomen Scan", 3500),
        ("SC004", "Upper Abdomen Scan", 3500),
        ("SC005", "Total / Full Abdominal Scan", 5000),
    ],
    "ECG": [
        ("EC001", "Pre-Exercise ECG", 10000),
        ("EC002", "Post-Exercise ECG", 10000),
        ("EC003", "Pre & Post Exercise ECG", 15000),
    ],
}

# Categories from the OLD placeholder catalog that are superseded by this official list
OLD_PLACEHOLDER_CATEGORIES = [
    "Laboratory Tests", "Imaging & Scans", "Health Packages", "Haematology",
    "Clinical Chemistry", "Blood Serology", "Microbiology & Parasitology",
    "Semen Analysis", "Skin Tests", "Ultrasound Scan", "Pregnancy Test",
    "Hormonal Profiles", "ECG",
]


class Command(BaseCommand):
    help = "Load/update the official Curex Diagnostic Center price list into the database."

    @transaction.atomic
    def handle(self, *args, **options):
        updated, created = 0, 0

        official_names = set()
        for category_name, items in OFFICIAL_PRICE_LIST.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for sku, name, price in items:
                official_names.add(name.lower())
                product, was_created = Product.objects.update_or_create(
                    name=name,
                    defaults=dict(
                        sku=sku,
                        category=category,
                        selling_price=price,
                        cost_price=round(price * 0.35),
                        stock_quantity=999,
                        low_stock_threshold=5,
                        expiry_date=None,
                        is_active=True,
                    ),
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        # Deactivate old placeholder-catalog products that aren't part of the official list,
        # so the site never shows stale/fictional prices alongside the real ones.
        deactivated = 0
        stale_products = Product.objects.filter(
            category__name__in=OLD_PLACEHOLDER_CATEGORIES, is_active=True
        ).exclude(name__in=[n for cat in OFFICIAL_PRICE_LIST.values() for _, n, _ in cat])
        for p in stale_products:
            if p.name.lower() not in official_names:
                p.is_active = False
                p.save(update_fields=["is_active"])
                deactivated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Official price list loaded: {created} created, {updated} updated, "
            f"{deactivated} old placeholder tests deactivated."
        ))
