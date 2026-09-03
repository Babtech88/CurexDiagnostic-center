from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import staff_required, collector_required, role_required
from inventory.models import Product, StockMovement
from sales.models import Sale, SaleItem
from .forms import WhatsAppOrderStartForm, DeliveryStatusForm
from .models import WhatsAppOrder, WhatsAppOrderItem, DeliveryRequest

CART_SESSION_KEY = "whatsapp_cart"


def _get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


# ---------- Public cart & WhatsApp checkout ----------

def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    qty = int(request.POST.get("quantity", 1) or 1)
    cart = _get_cart(request)
    cart[str(pk)] = cart.get(str(pk), 0) + max(qty, 1)
    _save_cart(request, cart)
    messages.success(request, f"Added {product.name} to your order.")
    return redirect("orders:cart_view")


def cart_view(request):
    cart = _get_cart(request)
    products = Product.objects.filter(pk__in=cart.keys())
    line_items = []
    total = 0
    for product in products:
        qty = cart.get(str(product.pk), 0)
        subtotal = product.current_price * qty
        total += subtotal
        line_items.append({"product": product, "quantity": qty, "subtotal": subtotal})
    return render(request, "storefront/cart.html", {"line_items": line_items, "total": total})


def cart_remove(request, pk):
    cart = _get_cart(request)
    cart.pop(str(pk), None)
    _save_cart(request, cart)
    return redirect("orders:cart_view")


def cart_checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Your order is empty.")
        return redirect("storefront:catalog")

    products = Product.objects.filter(pk__in=cart.keys())
    if request.method == "POST":
        form = WhatsAppOrderStartForm(request.POST)
        if form.is_valid():
            order = WhatsAppOrder.objects.create(
                customer_name=form.cleaned_data["customer_name"],
                customer_phone=form.cleaned_data["customer_phone"],
                wants_delivery=form.cleaned_data["wants_delivery"],
                delivery_address=form.cleaned_data.get("delivery_address", ""),
                notes=form.cleaned_data.get("notes", ""),
            )
            for product in products:
                qty = cart.get(str(product.pk), 0)
                if qty > 0:
                    WhatsAppOrderItem.objects.create(
                        order=order, product=product, quantity=qty, unit_price=product.current_price,
                    )
            if order.wants_delivery:
                DeliveryRequest.objects.create(
                    whatsapp_order=order,
                    recipient_name=order.customer_name,
                    phone_number=order.customer_phone,
                    address=order.delivery_address,
                )
            _save_cart(request, {})
            return redirect("orders:whatsapp_redirect", pk=order.pk)
    else:
        form = WhatsAppOrderStartForm()

    line_items = []
    total = 0
    for product in products:
        qty = cart.get(str(product.pk), 0)
        subtotal = product.current_price * qty
        total += subtotal
        line_items.append({"product": product, "quantity": qty, "subtotal": subtotal})

    return render(request, "storefront/checkout.html", {"form": form, "line_items": line_items, "total": total})


def whatsapp_redirect(request, pk):
    order = get_object_or_404(WhatsAppOrder, pk=pk)
    return render(request, "storefront/whatsapp_redirect.html", {"order": order, "wa_link": order.whatsapp_link()})


# ---------- Staff: WhatsApp order management ----------

@staff_required
def whatsapp_order_list(request):
    orders = WhatsAppOrder.objects.all().prefetch_related("items")
    status = request.GET.get("status", "")
    if status:
        orders = orders.filter(status=status)
    return render(request, "orders/whatsapp_order_list.html", {"orders": orders, "status": status})


@staff_required
def whatsapp_order_detail(request, pk):
    order = get_object_or_404(WhatsAppOrder, pk=pk)
    return render(request, "orders/whatsapp_order_detail.html", {"order": order, "wa_link": order.whatsapp_link()})


@staff_required
def whatsapp_order_set_status(request, pk, status):
    order = get_object_or_404(WhatsAppOrder, pk=pk)
    valid_statuses = dict(WhatsAppOrder.STATUS_CHOICES)
    if status in valid_statuses:
        order.status = status
        order.save(update_fields=["status"])
        messages.success(request, f"Order marked as {valid_statuses[status]}.")
    return redirect("orders:whatsapp_order_detail", pk=pk)


@staff_required
def whatsapp_order_convert_to_sale(request, pk):
    order = get_object_or_404(WhatsAppOrder, pk=pk)
    if order.resulting_sales.exists():
        messages.warning(request, "This order was already converted to a sale.")
        return redirect("orders:whatsapp_order_detail", pk=pk)

    for item in order.items.all():
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f"Not enough stock for {item.product.name}.")
            return redirect("orders:whatsapp_order_detail", pk=pk)

    sale = Sale.objects.create(
        cashier=request.user, customer=order.customer, payment_method=Sale.PAYMENT_CASH,
        source=Sale.SOURCE_WHATSAPP, whatsapp_order=order,
    )
    for item in order.items.all():
        SaleItem.objects.create(
            sale=sale, product=item.product, quantity=item.quantity,
            unit_price=item.unit_price, unit_cost=item.product.cost_price,
        )
        item.product.stock_quantity -= item.quantity
        item.product.save(update_fields=["stock_quantity"])
        StockMovement.objects.create(
            product=item.product, quantity_change=-item.quantity, reason=StockMovement.REASON_SALE,
            note=f"WhatsApp order #{order.id} -> Sale #{sale.id}", created_by=request.user,
        )
    order.status = WhatsAppOrder.STATUS_CONFIRMED
    order.save(update_fields=["status"])
    messages.success(request, f"Converted to Sale #{sale.id}.")
    return redirect("sales:sale_detail", pk=sale.id)


# ---------- Staff: Delivery management ----------

@role_required("admin", "manager", "delivery")
def delivery_list(request):
    deliveries = DeliveryRequest.objects.select_related("assigned_rider", "whatsapp_order")
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.role == "delivery" and not request.user.is_superuser:
        deliveries = deliveries.filter(assigned_rider=request.user)
    status = request.GET.get("status", "")
    if status:
        deliveries = deliveries.filter(status=status)
    return render(request, "orders/delivery_list.html", {"deliveries": deliveries, "status": status})


@role_required("admin", "manager", "delivery")
def delivery_update(request, pk):
    delivery = get_object_or_404(DeliveryRequest, pk=pk)
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.role == "delivery" and delivery.assigned_rider_id != request.user.id:
        messages.error(request, "You can only update collections assigned to you.")
        return redirect("orders:delivery_list")
    if request.method == "POST":
        form = DeliveryStatusForm(request.POST, instance=delivery)
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery updated.")
            return redirect("orders:delivery_list")
    else:
        form = DeliveryStatusForm(instance=delivery)
    return render(request, "orders/delivery_form.html", {"form": form, "delivery": delivery})
