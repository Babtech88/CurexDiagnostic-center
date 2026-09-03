from django.conf import settings
from django.utils import timezone

from inventory.models import Product
from . import ai_reply
from .models import Appointment, WhatsAppContact
from .notifications import notify_staff

GREETINGS = {"hi", "hello", "hey", "menu", "start", "good morning", "good afternoon", "good evening"}
CANCEL_WORDS = {"cancel", "stop", "back"}

INTERNAL_ONLY_CATEGORIES = ["Reagents & Kits", "Consumables"]

MAIN_MENU = (
    "\U0001F44B Welcome to {site_name}!\n"
    "\"{motto}\"\n\n"
    "How can we help you today? Reply with a number:\n"
    "1\ufe0f\u20e3 Book an Appointment\n"
    "2\ufe0f\u20e3 Check Test Prices\n"
    "3\ufe0f\u20e3 Check Availability\n"
    "4\ufe0f\u20e3 Our Location & Hours\n"
    "5\ufe0f\u20e3 Talk to a Staff Member\n\n"
    "Or just ask us anything in your own words - fasting instructions, how results are "
    "delivered, what a test involves, etc."
)

LOCATION_REPLY = (
    "\U0001F4CD {site_name}\n{address}\n\n"
    "\U0001F4DE {phone}\n\u2709\ufe0f {email}\n\n"
    "\U0001F552 Hours: {hours}\n\n"
    "Reply MENU to go back to the main menu."
)

HUMAN_HANDOFF_REPLY = (
    "\U0001F9D1\u200D\u2695\ufe0f No problem - one of our staff members will reply to you here shortly "
    "during our business hours ({hours}). Thank you for your patience!"
)

NOT_FOUND_REPLY = (
    "Sorry, we couldn't find a test matching \"{query}\". Could you try a different name, "
    "or reply 5 to speak with a staff member?"
)

FALLBACK_REPLY = (
    "Sorry, I didn't quite catch that. Reply MENU to see your options, or just type the name "
    "of a test you're looking for."
)


def _format_menu():
    return MAIN_MENU.format(site_name=settings.SITE_NAME, motto=settings.SITE_MOTTO)


def _format_location():
    return LOCATION_REPLY.format(
        site_name=settings.SITE_NAME, address=settings.SITE_ADDRESS,
        phone=settings.SITE_PHONE, email=settings.SITE_EMAIL, hours=settings.BUSINESS_HOURS,
    )


def _billable_products_qs():
    return Product.objects.filter(is_active=True).exclude(category__name__in=INTERNAL_ONLY_CATEGORIES)


def _search_tests(query, limit=5):
    return list(_billable_products_qs().filter(name__icontains=query.strip())[:limit])


def _format_test_results(products):
    lines = ["Here's what we found:\n"]
    for p in products:
        lines.append(f"\u2022 {p.name} \u2014 \u20a6{p.current_price:,.0f}")
    lines.append("\nReply with another test name to search again, or MENU for options.")
    return "\n".join(lines)


def _format_availability(products):
    lines = ["Availability:\n"]
    for p in products:
        if p.is_out_of_stock:
            status = "\u274c Currently unavailable"
        elif p.is_low_stock:
            status = "\u26a0\ufe0f Limited availability - book soon"
        else:
            status = "\u2705 Available"
        lines.append(f"\u2022 {p.name} \u2014 {status}")
    lines.append("\nReply with another test name to check again, or MENU for options.")
    return "\n".join(lines)


def _reset_booking_scratch(contact):
    contact.pending_product = None
    contact.pending_date_text = ""


def _start_booking(contact):
    contact.state = WhatsAppContact.STATE_BOOKING_SELECT_TEST
    _reset_booking_scratch(contact)
    contact.save(update_fields=["state", "pending_product", "pending_date_text"])
    return (
        "Great, let's get you booked in! Which test, scan, or package would you like to book? "
        "(e.g. \"FBC\", \"malaria\", \"obstetric scan\")\n\nReply CANCEL any time to stop."
    )


def _handle_booking_select_test(contact, cleaned):
    results = _search_tests(cleaned, limit=5)
    if not results:
        return (
            f"Sorry, we couldn't find a test matching \"{cleaned}\". Try another name, or reply "
            "CANCEL to stop."
        )
    if len(results) == 1:
        contact.pending_product = results[0]
        contact.state = WhatsAppContact.STATE_BOOKING_SELECT_DATE
        contact.save(update_fields=["pending_product", "state"])
        return (
            f"Got it - {results[0].name} (\u20a6{results[0].current_price:,.0f}). "
            "What date and time would you prefer? (e.g. \"Friday morning\" or \"Aug 5, 10am\")"
        )
    lines = ["A few tests matched - which one did you mean?\n"]
    for p in results:
        lines.append(f"\u2022 {p.name}")
    lines.append("\nReply with the exact test name, or CANCEL to stop.")
    return "\n".join(lines)


def _handle_booking_select_date(contact, cleaned):
    contact.pending_date_text = cleaned[:100]
    contact.state = WhatsAppContact.STATE_BOOKING_CONFIRM
    contact.save(update_fields=["pending_date_text", "state"])
    product_name = contact.pending_product.name if contact.pending_product else "your selected test"
    return (
        f"Please confirm:\n\U0001F9EA {product_name}\n\U0001F4C5 {contact.pending_date_text}\n\n"
        "Reply YES to confirm, or CANCEL to stop."
    )


def _handle_booking_confirm(contact, lowered, cleaned):
    if lowered not in {"yes", "y", "confirm", "ok", "okay"}:
        return "Reply YES to confirm this appointment request, or CANCEL to stop."

    appointment = Appointment.objects.create(
        contact=contact,
        product=contact.pending_product,
        preferred_date_text=contact.pending_date_text,
    )
    _reset_booking_scratch(contact)
    contact.state = WhatsAppContact.STATE_MENU
    contact.save(update_fields=["pending_product", "pending_date_text", "state"])

    notify_staff(
        subject=f"New appointment request from {contact.profile_name or contact.wa_id}",
        message=(
            f"Patient: {contact.profile_name or 'Unknown'} ({contact.wa_id})\n"
            f"Test: {appointment.product.name if appointment.product else 'Unspecified'}\n"
            f"Preferred date/time: {appointment.preferred_date_text}\n"
            f"Requested at: {timezone.now():%Y-%m-%d %H:%M}\n\n"
            "Review and confirm it in the staff dashboard under WhatsApp Bot Chats / Appointments."
        ),
    )

    return (
        "\u2705 Your appointment request has been sent! Our team will confirm the exact time "
        "with you here shortly. Reply MENU for anything else."
    )


def handle_incoming_message(contact: WhatsAppContact, text: str) -> str:
    """
    Core bot logic: given a contact and their incoming message text, decide the reply,
    update contact.state as a side effect, and return the reply text to send back.
    """
    cleaned = (text or "").strip()
    lowered = cleaned.lower()

    # Cancel/back out of any multi-step flow
    if lowered in CANCEL_WORDS and contact.state in {
        WhatsAppContact.STATE_BOOKING_SELECT_TEST,
        WhatsAppContact.STATE_BOOKING_SELECT_DATE,
        WhatsAppContact.STATE_BOOKING_CONFIRM,
    }:
        _reset_booking_scratch(contact)
        contact.state = WhatsAppContact.STATE_MENU
        contact.save(update_fields=["pending_product", "pending_date_text", "state"])
        return "No problem, booking cancelled. " + _format_menu()

    # Explicit reset to menu / greeting always takes priority
    if lowered in GREETINGS:
        _reset_booking_scratch(contact)
        contact.state = WhatsAppContact.STATE_MENU
        contact.needs_human = False
        contact.save(update_fields=["pending_product", "pending_date_text", "state", "needs_human"])
        return _format_menu()

    # If flagged for human follow-up, stay quiet except to acknowledge
    if contact.needs_human and contact.state == WhatsAppContact.STATE_NEEDS_HUMAN:
        return HUMAN_HANDOFF_REPLY.format(hours=settings.BUSINESS_HOURS)

    # --- Multi-step appointment booking flow ---
    if contact.state == WhatsAppContact.STATE_BOOKING_SELECT_TEST:
        return _handle_booking_select_test(contact, cleaned)
    if contact.state == WhatsAppContact.STATE_BOOKING_SELECT_DATE:
        return _handle_booking_select_date(contact, cleaned)
    if contact.state == WhatsAppContact.STATE_BOOKING_CONFIRM:
        return _handle_booking_confirm(contact, lowered, cleaned)

    # --- Main menu selections ---
    if lowered in {"1", "1\ufe0f\u20e3"}:
        return _start_booking(contact)

    if lowered in {"2", "2\ufe0f\u20e3"}:
        contact.state = WhatsAppContact.STATE_AWAITING_TEST_QUERY
        contact.save(update_fields=["state"])
        return "Sure - which test, scan, or panel would you like the price for? (e.g. \"FBC\", \"malaria\", \"ultrasound\")"

    if lowered in {"3", "3\ufe0f\u20e3"}:
        contact.state = WhatsAppContact.STATE_AWAITING_AVAILABILITY_QUERY
        contact.save(update_fields=["state"])
        return "Which test would you like to check availability for?"

    if lowered in {"4", "4\ufe0f\u20e3"}:
        contact.state = WhatsAppContact.STATE_MENU
        contact.save(update_fields=["state"])
        return _format_location()

    if lowered in {"5", "5\ufe0f\u20e3"}:
        contact.state = WhatsAppContact.STATE_NEEDS_HUMAN
        contact.needs_human = True
        contact.save(update_fields=["state", "needs_human"])
        notify_staff(
            subject=f"Patient needs a human - {contact.profile_name or contact.wa_id}",
            message=(
                f"Patient: {contact.profile_name or 'Unknown'} ({contact.wa_id}) has asked to "
                f"speak with a staff member. Reply to them in the dashboard under WhatsApp Bot "
                f"Chats, or directly on WhatsApp."
            ),
        )
        return HUMAN_HANDOFF_REPLY.format(hours=settings.BUSINESS_HOURS)

    # --- Follow-up states from menu options 2 / 3 ---
    if contact.state == WhatsAppContact.STATE_AWAITING_TEST_QUERY:
        results = _search_tests(cleaned)
        contact.state = WhatsAppContact.STATE_MENU
        contact.save(update_fields=["state"])
        return _format_test_results(results) if results else NOT_FOUND_REPLY.format(query=cleaned)

    if contact.state == WhatsAppContact.STATE_AWAITING_AVAILABILITY_QUERY:
        results = _search_tests(cleaned)
        contact.state = WhatsAppContact.STATE_MENU
        contact.save(update_fields=["state"])
        return _format_availability(results) if results else NOT_FOUND_REPLY.format(query=cleaned)

    # Free-text test name match even outside a specific flow
    if len(cleaned) >= 3:
        results = _search_tests(cleaned)
        if results:
            contact.state = WhatsAppContact.STATE_MENU
            contact.save(update_fields=["state"])
            return _format_test_results(results)

    # AI-powered fallback for anything else, if configured
    ai_text = ai_reply.get_ai_reply(cleaned) if cleaned else None
    if ai_text:
        return ai_text + "\n\nReply MENU any time for quick options."

    return FALLBACK_REPLY
