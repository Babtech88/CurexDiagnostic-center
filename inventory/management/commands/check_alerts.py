from django.core.management.base import BaseCommand
from django.core.mail import mail_admins

from inventory.models import Product


class Command(BaseCommand):
    help = "Check for low-stock and expiring/expired products, and email admins a summary. Intended to run daily via cron/celery-beat."

    def handle(self, *args, **options):
        products = Product.objects.filter(is_active=True)
        low_stock = [p for p in products if p.is_low_stock]
        expiring = [p for p in products if p.is_expiring_soon and not p.is_expired]
        expired = [p for p in products if p.is_expired]

        lines = []
        if low_stock:
            lines.append("LOW STOCK:")
            lines += [f"  - {p.name}: {p.stock_quantity} left (threshold {p.low_stock_threshold})" for p in low_stock]
        if expiring:
            lines.append("EXPIRING SOON:")
            lines += [f"  - {p.name}: expires {p.expiry_date} ({p.days_to_expiry} days)" for p in expiring]
        if expired:
            lines.append("EXPIRED:")
            lines += [f"  - {p.name}: expired {p.expiry_date}" for p in expired]

        if not lines:
            self.stdout.write(self.style.SUCCESS("No alerts today — all stock levels and expiry dates look healthy."))
            return

        message = "\n".join(lines)
        self.stdout.write(message)

        try:
            mail_admins("BabsBooks Store — Daily Stock & Expiry Alerts", message, fail_silently=True)
        except Exception as e:
            self.stderr.write(f"Could not send alert email: {e}")

        self.stdout.write(self.style.WARNING(
            f"\n{len(low_stock)} low stock, {len(expiring)} expiring soon, {len(expired)} expired."
        ))
