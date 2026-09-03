import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Prefetch
from django.views.decorators.csrf import csrf_exempt

from accounts.permissions import staff_required, sales_manager_required
from .bot_engine import handle_incoming_message
from .models import Appointment, WhatsAppContact, WhatsAppMessageLog
from customers.models import Customer
from inventory.models import Product
from orders.models import WhatsAppOrder, WhatsAppOrderItem, DeliveryRequest
from sales.models import Sale
from .services import WhatsAppSendError, send_whatsapp_text

logger = logging.getLogger(__name__)


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        return _verify_webhook(request)
    if request.method == "POST":
        return _receive_webhook(request)
    return HttpResponse(status=405)


def _verify_webhook(request):
    """Meta calls this once when you configure the webhook URL in the developer dashboard."""
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return HttpResponse(challenge)
    return HttpResponseForbidden("Verification failed")


def _receive_webhook(request):
    """Handle an incoming message event from WhatsApp Cloud API."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("WhatsApp webhook received invalid JSON body")
        return JsonResponse({"status": "ignored"}, status=200)

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts_meta = {c["wa_id"]: c.get("profile", {}).get("name", "") for c in value.get("contacts", [])}

                for message in messages:
                    _process_single_message(message, contacts_meta)
    except Exception:
        # Never let a malformed/unexpected payload crash the webhook — Meta will retry on non-2xx.
        logger.exception("Error processing WhatsApp webhook payload")

    # Always acknowledge quickly with 200 so Meta doesn't retry/backoff.
    return JsonResponse({"status": "received"}, status=200)


def _process_single_message(message, contacts_meta):
    wa_id = message.get("from")
    if not wa_id:
        return

    msg_type = message.get("type")
    if msg_type == "text":
        body = message.get("text", {}).get("body", "")
    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        body = (
            interactive.get("button_reply", {}).get("title")
            or interactive.get("list_reply", {}).get("title")
            or ""
        )
    else:
        # Non-text message (image, audio, location, etc.) — acknowledge generically.
        body = f"[{msg_type} message received]"

    contact, _ = WhatsAppContact.objects.get_or_create(
        wa_id=wa_id, defaults={"profile_name": contacts_meta.get(wa_id, "")}
    )
    if contacts_meta.get(wa_id) and not contact.profile_name:
        contact.profile_name = contacts_meta[wa_id]
        contact.save(update_fields=["profile_name"])

    WhatsAppMessageLog.objects.create(
        contact=contact, direction=WhatsAppMessageLog.DIRECTION_IN,
        body=body, wa_message_id=message.get("id", ""),
    )
    contact.unread_count = (contact.unread_count or 0) + 1
    contact.last_seen = timezone.now()
    contact.save(update_fields=["unread_count", "last_seen"])

    # Once a human owns the conversation, incoming messages are logged but the bot stays silent.
    if contact.needs_human or contact.assigned_agent_id:
        return

    # The bot is enabled by default and can be switched off with WHATSAPP_BOT_ENABLED=False.
    if not getattr(settings, "WHATSAPP_BOT_ENABLED", True):
        logger.info("WhatsApp bot is disabled; incoming message logged without auto-reply.")
        return

    reply_text = handle_incoming_message(contact, body)

    WhatsAppMessageLog.objects.create(
        contact=contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=reply_text,
    )

    try:
        send_whatsapp_text(wa_id, reply_text)
    except WhatsAppSendError:
        logger.error("Could not deliver auto-reply to %s (check WHATSAPP_CLOUD_API_TOKEN)", wa_id)


@staff_required
def bot_status(request):
    """Show the active WhatsApp booking mode. Assisted mode needs no Meta API."""
    mode = getattr(settings, "WHATSAPP_MODE", "assisted")
    assisted = bool(getattr(settings, "WHATSAPP_ASSISTED_MODE", False))
    business_number = getattr(settings, "WHATSAPP_BUSINESS_NUMBER", "")
    ready = assisted and bool(business_number)
    return render(request, "whatsapp_bot/status.html", {
        "mode": mode,
        "assisted": assisted,
        "enabled": bool(getattr(settings, "WHATSAPP_BOT_ENABLED", True)),
        "business_number": business_number,
        "ready": ready,
    })


# ---------- Staff-facing conversation viewer ----------

@staff_required
def conversation_list(request):
    contacts = WhatsAppContact.objects.select_related("assigned_agent", "linked_patient").prefetch_related(
        Prefetch("messages", queryset=WhatsAppMessageLog.objects.order_by("-created_at"))
    )
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.is_sales_agent and not request.user.is_superuser:
        contacts = contacts.filter(assigned_agent=request.user)

    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()
    if status in {"open", "pending", "resolved"}:
        contacts = contacts.filter(conversation_status=status)
    if request.GET.get("needs_human") == "1":
        contacts = contacts.filter(needs_human=True)
    if search:
        contacts = contacts.filter(Q(profile_name__icontains=search) | Q(wa_id__icontains=search))

    contacts = contacts.order_by("-unread_count", "-last_seen")
    return render(request, "whatsapp_bot/conversation_list.html", {
        "contacts": contacts, "status": status, "search": search,
    })


@staff_required
def conversation_detail(request, pk):
    profile = getattr(request.user, "staff_profile", None)
    contact = get_object_or_404(
        WhatsAppContact.objects.select_related("assigned_agent", "linked_patient"), pk=pk
    )
    if profile and profile.is_sales_agent and not request.user.is_superuser and contact.assigned_agent_id != request.user.id:
        return HttpResponseForbidden("This conversation is not assigned to you.")

    if request.method == "POST":
        action = request.POST.get("action", "reply")
        if action == "reply":
            text = request.POST.get("reply", "").strip()
            if text:
                if getattr(settings, "WHATSAPP_ASSISTED_MODE", False):
                    from urllib.parse import quote
                    WhatsAppMessageLog.objects.create(contact=contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=text)
                    contact.needs_human = False
                    contact.conversation_status = WhatsAppContact.STATUS_OPEN
                    contact.state = WhatsAppContact.STATE_MENU
                    contact.save(update_fields=["needs_human", "conversation_status", "state"])
                    return redirect(f"https://wa.me/{contact.wa_id}?text={quote(text)}")
                try:
                    send_whatsapp_text(contact.wa_id, text)
                except WhatsAppSendError:
                    messages.error(request, "Message could not be delivered. Check the WhatsApp connection.")
                else:
                    WhatsAppMessageLog.objects.create(contact=contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=text)
                    contact.needs_human = False
                    contact.conversation_status = WhatsAppContact.STATUS_OPEN
                    contact.state = WhatsAppContact.STATE_MENU
                    contact.save(update_fields=["needs_human", "conversation_status", "state"])
                    messages.success(request, "Message sent.")
        elif action == "status":
            new_status = request.POST.get("conversation_status")
            if new_status in dict(WhatsAppContact.STATUS_CHOICES):
                contact.conversation_status = new_status
                if new_status == WhatsAppContact.STATUS_RESOLVED:
                    contact.needs_human = False
                contact.save(update_fields=["conversation_status", "needs_human"])
        elif action == "mark_read":
            contact.unread_count = 0
            contact.save(update_fields=["unread_count"])
        elif action == "create_order":
            _create_order_from_conversation(request, contact)
            return redirect("whatsapp_bot:conversation_detail", pk=contact.pk)
        elif action == "payment":
            order = get_object_or_404(WhatsAppOrder, pk=request.POST.get("order_id"), contact=contact)
            payment_status = request.POST.get("payment_status")
            if payment_status in dict(WhatsAppOrder.PAYMENT_CHOICES):
                order.payment_status = payment_status
                order.payment_reference = request.POST.get("payment_reference", "").strip()
                order.save(update_fields=["payment_status", "payment_reference"])
                messages.success(request, "Payment status updated.")
        elif action == "convert_sale":
            order = get_object_or_404(WhatsAppOrder, pk=request.POST.get("order_id"), contact=contact)
            _convert_whatsapp_order_to_sale(request, order)
            return redirect("whatsapp_bot:conversation_detail", pk=contact.pk)

    contact.unread_count = 0
    contact.save(update_fields=["unread_count"])
    messages_qs = contact.messages.all()
    orders = contact.orders.select_related("customer").prefetch_related("items__product").all()
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).order_by("name")
    sales_users = _sales_users()
    return render(request, "whatsapp_bot/conversation_detail.html", {
        "contact": contact, "messages": messages_qs, "sales_users": sales_users,
        "products": products, "orders": orders,
    })


def _sales_users():
    from django.contrib.auth.models import User
    return User.objects.filter(
        is_active=True,
        staff_profile__role__in={"sales_agent", "sales_manager", "manager", "admin"},
    ).select_related("staff_profile").order_by("first_name", "last_name", "username")


def _get_or_create_customer(contact):
    customer = contact.linked_patient
    if customer:
        changed = False
        if not customer.phone_number:
            customer.phone_number = contact.wa_id; changed = True
        if not customer.name and contact.profile_name:
            customer.name = contact.profile_name; changed = True
        if changed:
            customer.save(update_fields=["phone_number", "name"])
        return customer
    customer = Customer.objects.filter(phone_number=contact.wa_id).first()
    if not customer:
        customer = Customer.objects.create(
            name=contact.profile_name or "WhatsApp Customer",
            phone_number=contact.wa_id,
        )
    contact.linked_patient = customer
    contact.save(update_fields=["linked_patient"])
    return customer


def _create_order_from_conversation(request, contact):
    product_ids = request.POST.getlist("product_id")
    quantities = request.POST.getlist("quantity")
    selected = []
    for product_id, qty_raw in zip(product_ids, quantities):
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if product:
            if qty > product.stock_quantity:
                messages.error(request, f"Not enough stock for {product.name}.")
                return
            selected.append((product, qty))
    if not selected:
        messages.error(request, "Select at least one product/service.")
        return
    customer = _get_or_create_customer(contact)
    order = WhatsAppOrder.objects.create(
        contact=contact,
        customer=customer,
        customer_name=customer.name,
        customer_phone=customer.phone_number,
        wants_delivery=request.POST.get("wants_delivery") == "1",
        delivery_address=request.POST.get("delivery_address", "").strip(),
        notes=request.POST.get("notes", "").strip(),
    )
    for product, qty in selected:
        WhatsAppOrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=product.current_price)
    contact.conversation_status = WhatsAppContact.STATUS_PENDING
    contact.needs_human = True
    contact.save(update_fields=["conversation_status", "needs_human"])
    messages.success(request, f"WhatsApp order #{order.id} created for ₦{order.total_amount:,.2f}.")


@transaction.atomic
def _convert_whatsapp_order_to_sale(request, order):
    if order.resulting_sales.exists():
        messages.warning(request, "This order has already been converted to a sale.")
        return
    if order.payment_status != WhatsAppOrder.PAYMENT_PAID:
        messages.error(request, "Mark the order as paid before converting it to a completed sale.")
        return
    for item in order.items.select_related("product"):
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f"Not enough stock for {item.product.name}.")
            return
    sale = Sale.objects.create(
        cashier=request.user, customer=order.customer, payment_method=request.POST.get("payment_method") if request.POST.get("payment_method") in dict(Sale.PAYMENT_CHOICES) else Sale.PAYMENT_TRANSFER,
        source=Sale.SOURCE_WHATSAPP, whatsapp_order=order,
    )
    from inventory.models import StockMovement
    for item in order.items.select_related("product"):
        from sales.models import SaleItem
        SaleItem.objects.create(
            sale=sale, product=item.product, quantity=item.quantity,
            unit_price=item.unit_price, unit_cost=item.product.cost_price,
        )
        item.product.stock_quantity -= item.quantity
        item.product.save(update_fields=["stock_quantity"])
        StockMovement.objects.create(
            product=item.product, quantity_change=-item.quantity,
            reason=StockMovement.REASON_SALE,
            note=f"WhatsApp workspace order #{order.id} -> Sale #{sale.id}", created_by=request.user,
        )
    order.status = WhatsAppOrder.STATUS_FULFILLED
    order.save(update_fields=["status"])
    if order.wants_delivery and order.delivery_address:
        DeliveryRequest.objects.get_or_create(
            whatsapp_order=order,
            defaults={
                "sale": sale,
                "recipient_name": order.customer_name,
                "phone_number": order.customer_phone,
                "address": order.delivery_address,
            },
        )
    messages.success(request, f"Order #{order.id} converted to completed Sale #{sale.id}.")


@sales_manager_required
def assign_conversation(request, pk):
    if request.method != "POST":
        return redirect("whatsapp_bot:conversation_list")
    contact = get_object_or_404(WhatsAppContact, pk=pk)
    agent_id = request.POST.get("assigned_agent", "").strip()
    if agent_id:
        agent = get_object_or_404(_sales_users(), pk=agent_id)
        contact.assigned_agent = agent
        contact.needs_human = True
        contact.conversation_status = WhatsAppContact.STATUS_PENDING
    else:
        contact.assigned_agent = None
    contact.save(update_fields=["assigned_agent", "needs_human", "conversation_status"])
    return redirect("whatsapp_bot:conversation_detail", pk=contact.pk)


# ---------- Staff-facing appointment management ----------

@staff_required
def appointment_list(request):
    appointments = Appointment.objects.select_related("contact", "product").all()
    status = request.GET.get("status", "")
    if status:
        appointments = appointments.filter(status=status)
    return render(request, "whatsapp_bot/appointment_list.html", {"appointments": appointments, "status": status})


@staff_required
def appointment_set_status(request, pk, status):
    appointment = get_object_or_404(Appointment, pk=pk)
    valid_statuses = dict(Appointment.STATUS_CHOICES)
    if status in valid_statuses:
        appointment.status = status
        appointment.save(update_fields=["status"])

        if status == Appointment.STATUS_CONFIRMED:
            product_name = appointment.product.name if appointment.product else "your test"
            confirm_text = (
                f"\u2705 Your appointment for {product_name} on {appointment.preferred_date_text} "
                f"has been confirmed! See you then.\n\n{settings.SITE_NAME}\n{settings.SITE_ADDRESS}"
            )
            WhatsAppMessageLog.objects.create(
                contact=appointment.contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=confirm_text,
            )
            try:
                send_whatsapp_text(appointment.contact.wa_id, confirm_text)
            except WhatsAppSendError:
                logger.error("Could not notify patient of confirmed appointment %s", appointment.pk)

    return redirect("whatsapp_bot:appointment_list")
