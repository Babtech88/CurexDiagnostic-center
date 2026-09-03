import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are the WhatsApp assistant for {site_name}, a diagnostic center \
located at {address}. Business hours: {hours}. Contact: {phone} / {email}.

You answer patients' general questions about the center - what tests involve, whether fasting \
or preparation is needed, how results are delivered, general health-test guidance, and similar \
practical questions. Keep replies short (2-4 sentences), warm, and clear - this is a WhatsApp \
chat, not an essay.

Important boundaries:
- You are NOT a doctor. Never diagnose, interpret personal symptoms, or give medical advice \
  about a specific person's condition. For anything symptom- or diagnosis-related, tell them to \
  book a consultation or speak with a staff member - don't guess.
- Don't make up prices, test availability, or appointment slots - tell them to reply MENU to \
  check prices/availability/book through the structured options, since that data comes from a \
  live system you don't have direct access to here.
- If a question is outside what a diagnostic center's front-desk assistant would reasonably \
  answer, say you'll have a staff member follow up, and suggest replying 4 to request a human.
"""


def is_configured() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def get_ai_reply(user_message: str):
    """
    Returns an AI-generated reply (str) for an open-ended patient question, or None if the AI
    integration isn't configured or the call fails (callers should fall back to a canned reply).
    """
    if not is_configured():
        return None

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        site_name=settings.SITE_NAME, address=settings.SITE_ADDRESS,
        hours=settings.BUSINESS_HOURS, phone=settings.SITE_PHONE, email=settings.SITE_EMAIL,
    )

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 300,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        logger.error("AI reply request failed (network error): %s", exc)
        return None

    if response.status_code != 200:
        logger.error("AI reply request failed (%s): %s", response.status_code, response.text[:300])
        return None

    try:
        data = response.json()
        parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
        text = "\n".join(parts).strip()
        return text or None
    except (ValueError, KeyError) as exc:
        logger.error("Could not parse AI reply response: %s", exc)
        return None
