import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppSendError(Exception):
    pass


def send_whatsapp_text(to_wa_id: str, body: str) -> dict:
    """
    Send a plain-text WhatsApp message via Meta's Cloud API.
    `to_wa_id` should be the recipient's number in international format, no '+' (e.g. '2348012345678').
    Raises WhatsAppSendError on failure; returns the parsed JSON response on success.
    """
    if not getattr(settings, "WHATSAPP_BOT_ENABLED", True):
        raise WhatsAppSendError("WhatsApp bot is disabled by WHATSAPP_BOT_ENABLED.")
    if not settings.WHATSAPP_CLOUD_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise WhatsAppSendError("WhatsApp Cloud API credentials are not configured.")

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_CLOUD_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": body},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException as exc:
        logger.error("WhatsApp send failed (network error) to %s: %s", to_wa_id, exc)
        raise WhatsAppSendError(str(exc)) from exc

    if response.status_code >= 300:
        logger.error("WhatsApp send failed (%s) to %s: %s", response.status_code, to_wa_id, response.text)
        raise WhatsAppSendError(f"{response.status_code}: {response.text}")

    return response.json()
