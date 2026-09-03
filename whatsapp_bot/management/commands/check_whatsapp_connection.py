from django.conf import settings
from django.core.management.base import BaseCommand

import requests


class Command(BaseCommand):
    help = "Verify WHATSAPP_CLOUD_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID are valid by calling the Graph API."

    def handle(self, *args, **options):
        if not settings.WHATSAPP_CLOUD_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            self.stderr.write(self.style.ERROR(
                "WHATSAPP_CLOUD_API_TOKEN or WHATSAPP_PHONE_NUMBER_ID is not set. Check your .env file."
            ))
            return

        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_CLOUD_API_TOKEN}"}

        self.stdout.write(f"Calling {url} ...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
        except requests.RequestException as exc:
            self.stderr.write(self.style.ERROR(f"Network error: {exc}"))
            return

        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("✅ Credentials are valid!"))
            self.stdout.write(f"  Display name: {data.get('verified_name', 'n/a')}")
            self.stdout.write(f"  Phone number: {data.get('display_phone_number', 'n/a')}")
            self.stdout.write(f"  Quality rating: {data.get('quality_rating', 'n/a')}")
        else:
            self.stderr.write(self.style.ERROR(f"❌ Request failed ({response.status_code}):"))
            self.stderr.write(response.text)
            self.stdout.write(
                "\nCommon causes: token expired/revoked, wrong Phone Number ID, or the token's "
                "System User isn't assigned to this WhatsApp app with the right permission."
            )
