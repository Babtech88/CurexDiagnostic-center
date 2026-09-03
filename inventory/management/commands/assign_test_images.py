"""
Assigns a category-appropriate illustration to every test/product that doesn't already have
an image. Images live in static/img/categories/ (generated originals, not stock photos) and
get copied into MEDIA_ROOT once per category, then referenced by every product in that category.
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from inventory.models import Product

CATEGORY_IMAGE_MAP = {
    "Clinical Chemistry": "clinical-chemistry.jpg",
    "Haematology & Blood Group Serology": "haematology.jpg",
    "Microbiology": "microbiology.jpg",
    "Scan": "scan.jpg",
    "ECG": "ecg.jpg",
    "Reagents & Kits": "general.jpg",
    "Consumables": "general.jpg",
}


class Command(BaseCommand):
    help = "Assign a category illustration to every product missing an image."

    def handle(self, *args, **options):
        source_dir = Path(settings.BASE_DIR) / "static" / "img" / "categories"
        media_dir = Path(settings.MEDIA_ROOT) / "products" / "category_images"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Copy each source image into MEDIA_ROOT once (products will share these files by name)
        copied = {}
        for category_name, filename in CATEGORY_IMAGE_MAP.items():
            src = source_dir / filename
            if not src.exists():
                continue
            dst = media_dir / filename
            if not dst.exists():
                shutil.copy(src, dst)
            copied[category_name] = f"products/category_images/{filename}"

        updated = 0
        for product in Product.objects.select_related("category").all():
            if product.image:
                continue
            category_name = product.category.name if product.category else None
            relative_path = copied.get(category_name)
            if not relative_path:
                continue
            product.image.name = relative_path
            product.save(update_fields=["image"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Assigned images to {updated} products."))
