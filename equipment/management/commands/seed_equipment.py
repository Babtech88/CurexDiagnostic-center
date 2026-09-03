import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from equipment.models import Equipment

EQUIPMENT_DATA = [
    # name, type, location, photo_filename (from static/img/equipment or categories), status, next_maintenance_days
    ("H-7034 Hematology Analyzer", "5-Part-Diff Hematology Analyzer", "Lab Room 1", "haematology.jpg", Equipment.STATUS_OPERATIONAL, 60),
    ("Blood Chemistry Analyzer", "Clinical Chemistry Analyzer", "Lab Room 1", "clinical-chemistry.jpg", Equipment.STATUS_OPERATIONAL, 45),
    ("Digital Ultrasound Scanner", "Ultrasound Imaging System", "Scan Room", "ultrasound-scanner.jpg", Equipment.STATUS_OPERATIONAL, 90),
    ("Exercise Stress ECG System", "Cardiac Monitoring Equipment", "ECG Room", "ecg.jpg", Equipment.STATUS_NEEDS_MAINTENANCE, -5),
    ("Rapid Test Kit Storage", "Microbiology / Rapid Test Kits", "Lab Room 2", "microbiology.jpg", Equipment.STATUS_OPERATIONAL, 30),
    ("Blood Culture System", "Culture & Sensitivity Equipment", "Lab Room 2", None, Equipment.STATUS_OPERATIONAL, 75),
]


class Command(BaseCommand):
    help = "Seed the Equipment Monitor with the center's real equipment."

    def handle(self, *args, **options):
        today = timezone.localdate()
        categories_dir = Path(settings.BASE_DIR) / "static" / "img" / "categories"
        equipment_dir = Path(settings.BASE_DIR) / "static" / "img" / "equipment"
        media_dir = Path(settings.MEDIA_ROOT) / "equipment_photos"
        media_dir.mkdir(parents=True, exist_ok=True)

        created = 0
        for name, etype, location, photo_file, status, maintenance_days in EQUIPMENT_DATA:
            if Equipment.objects.filter(name=name).exists():
                continue

            item = Equipment(
                name=name, equipment_type=etype, location=location, status=status,
                last_serviced_date=today - timedelta(days=90 - maintenance_days if maintenance_days > 0 else 95),
                next_maintenance_date=today + timedelta(days=maintenance_days),
            )

            if photo_file:
                src = categories_dir / photo_file
                if not src.exists():
                    src = equipment_dir / photo_file
                if src.exists():
                    dst = media_dir / photo_file
                    if not dst.exists():
                        shutil.copy(src, dst)
                    item.photo.name = f"equipment_photos/{photo_file}"

            item.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} equipment items."))
