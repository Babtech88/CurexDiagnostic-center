import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_staff(subject: str, message: str) -> None:
    """
    Email everyone in STAFF_NOTIFICATION_EMAILS. Safe to call even if that list is empty —
    it just logs and does nothing (rather than raising), so it never breaks the bot reply flow.
    """
    recipients = settings.STAFF_NOTIFICATION_EMAILS
    if not recipients:
        logger.info("STAFF_NOTIFICATION_EMAILS not configured — skipping notification: %s", subject)
        return

    try:
        send_mail(
            subject=f"[Curex Bot] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send staff notification email: %s", subject)
