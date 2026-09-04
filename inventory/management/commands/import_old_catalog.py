import os
import sqlite3
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Category, Product


class Command(BaseCommand):
    help = "Import categories and products from the old SQLite database"

    def handle(self, *args, **options):
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )

        sqlite_path = os.path.join(base_dir, "old_catalog.sqlite3")

        if not os.path.exists(sqlite_path):
            self.stderr.write(
                self.style.ERROR(
                    f"Old SQLite database not found: {sqlite_path}"
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Reading old database: {sqlite_path}"
            )
        )

        old_db = sqlite3.connect(sqlite_path)
        old_db.row_factory = sqlite3.Row
        cursor = old_db.cursor()

        try:
            with transaction.atomic():

                # ==========================
                # IMPORT CATEGORIES
                # ==========================

                cursor.execute("""
                    SELECT id, name, description
                    FROM inventory_category
                    ORDER BY id
                """)

                categories = cursor.fetchall()

                category_map = {}

                for category in categories:
                    new_category, created = Category.objects.update_or_create(
                        name=category["name"],
                        defaults={
                            "description": category["description"] or "",
                        },
                    )

                    category_map[category["id"]] = new_category

                    status = "Created" if created else "Updated"

                    self.stdout.write(
                        f"{status} category: {new_category.name}"
                    )

                # ==========================
                # IMPORT PRODUCTS
                # ==========================

                cursor.execute("""
                    SELECT
                        id,
                        name,
                        sku,
                        description,
                        image,
                        cost_price,
                        selling_price,
                        stock_quantity,
                        low_stock_threshold,
                        expiry_date,
                        is_active,
                        category_id
                    FROM inventory_product
                    ORDER BY id
                """)

                products = cursor.fetchall()

                created_count = 0
                updated_count = 0

                for product in products:

                    category = None

                    if product["category_id"]:
                        category = category_map.get(
                            product["category_id"]
                        )

                    defaults = {
                        "name": product["name"],
                        "description": product["description"] or "",
                        "image": product["image"] or "",
                        "cost_price": Decimal(
                            str(product["cost_price"])
                        ),
                        "selling_price": Decimal(
                            str(product["selling_price"])
                        ),
                        "stock_quantity": product["stock_quantity"],
                        "low_stock_threshold": (
                            product["low_stock_threshold"]
                        ),
                        "expiry_date": product["expiry_date"],
                        "is_active": bool(product["is_active"]),
                        "category": category,
                    }

                    new_product, created = (
                        Product.objects.update_or_create(
                            sku=product["sku"],
                            defaults=defaults,
                        )
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    self.stdout.write(
                        f"{'Created' if created else 'Updated'}: "
                        f"{new_product.name}"
                    )

        finally:
            old_db.close()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Catalog import completed successfully!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Categories imported: {Category.objects.count()}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Products created: {created_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Products updated: {updated_count}"
            )
        )