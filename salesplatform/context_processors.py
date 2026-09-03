from django.conf import settings


def business_identity(request):
    return {
        "site_name": settings.SITE_NAME,
        "site_motto": settings.SITE_MOTTO,
        "site_address": settings.SITE_ADDRESS,
        "site_phone": settings.SITE_PHONE,
        "site_email": settings.SITE_EMAIL,
        "whatsapp_number": settings.WHATSAPP_BUSINESS_NUMBER,
        "business_hours": settings.BUSINESS_HOURS,
        "site_facebook": getattr(settings, "SITE_FACEBOOK", ""),
        "site_instagram": getattr(settings, "SITE_INSTAGRAM", ""),
        "site_twitter": getattr(settings, "SITE_TWITTER", ""),
    }
