"""
Shared conversation-state constants for the bot brain (whatsapp_bot/bot_engine.py), used by
the WhatsApp bot conversation flow.

These string values are part of the database schema (stored in each model's `state` field) —
don't change existing values without a data migration.
"""

STATE_NEW = "new"
STATE_MENU = "menu"
STATE_AWAITING_TEST_QUERY = "awaiting_test_query"
STATE_AWAITING_AVAILABILITY_QUERY = "awaiting_availability_query"
STATE_AWAITING_SYMPTOM_DESCRIPTION = "awaiting_symptom_description"
STATE_BOOKING_SELECT_TEST = "booking_select_test"
STATE_BOOKING_SELECT_DATE = "booking_select_date"
STATE_BOOKING_CONFIRM = "booking_confirm"
STATE_NEEDS_HUMAN = "needs_human"

STATE_CHOICES = [
    (STATE_NEW, "New"),
    (STATE_MENU, "At Main Menu"),
    (STATE_AWAITING_TEST_QUERY, "Awaiting Test Name"),
    (STATE_AWAITING_AVAILABILITY_QUERY, "Awaiting Availability Query"),
    (STATE_AWAITING_SYMPTOM_DESCRIPTION, "Awaiting Symptom Description"),
    (STATE_BOOKING_SELECT_TEST, "Booking: Choosing Test"),
    (STATE_BOOKING_SELECT_DATE, "Booking: Choosing Date"),
    (STATE_BOOKING_CONFIRM, "Booking: Awaiting Confirmation"),
    (STATE_NEEDS_HUMAN, "Needs Human Follow-up"),
]

CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_CHOICES = [(CHANNEL_WHATSAPP, "WhatsApp")]
