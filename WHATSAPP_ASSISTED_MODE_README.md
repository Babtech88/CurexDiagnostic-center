# Curex WhatsApp Assisted Booking Mode

This version is configured to use the WhatsApp application / WhatsApp Web rather than the Meta Cloud API.

## What customers do
1. Browse diagnostic tests.
2. Add tests to the cart.
3. Complete the booking form.
4. Click **Open WhatsApp to Confirm**.
5. WhatsApp opens with the booking details already filled in.

## What staff do
- Use the **WhatsApp Bookings** workspace to review saved bookings.
- Click **Message Patient on WhatsApp** to continue the conversation manually.
- Update booking status and payment status.
- Convert a confirmed booking into a sale when appropriate.

## No Meta API setup is required
The project runs with:

    WHATSAPP_MODE=assisted

The old Meta Cloud API credentials are not required for this mode.

## Database migration
This package also includes an orders migration that adds the missing `payment_status` and `payment_reference` fields to `DeliveryRequest`.
Run:

    python manage.py migrate

before using checkout.
