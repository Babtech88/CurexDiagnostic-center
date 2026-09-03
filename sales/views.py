import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import staff_required, manager_required
from customers.models import Customer
from inventory.models import Product, StockMovement, Category
from .forms import NewSaleForm
from .models import Sale, SaleItem


@staff_required
def pos_new_sale(request):
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related("category").order_by("category__name", "name")
    categories = Category.objects.filter(products__in=products).distinct().order_by("name")
    if request.method == "POST":
        form = NewSaleForm(request.POST)
        if form.is_valid():
            line_items = []
            for product in products:
                qty_raw = request.POST.get(f"qty_{product.id}", "0")
                try:
                    qty = int(qty_raw)
                except ValueError:
                    qty = 0
                if qty > 0:
                    if qty > product.stock_quantity:
                        messages.error(request, f"Not enough stock for {product.name} (only {product.stock_quantity} left).")
                        return render(request, "sales/pos.html", {"form": form, "products": products, "categories": categories})
                    line_items.append((product, qty))

            if not line_items:
                messages.error(request, "Add at least one product with a quantity.")
                return render(request, "sales/pos.html", {"form": form, "products": products, "categories": categories})

            sale = Sale.objects.create(
                cashier=request.user,
                customer=form.cleaned_data.get("customer"),
                payment_method=form.cleaned_data["payment_method"],
                source=Sale.SOURCE_IN_STORE,
            )
            for product, qty in line_items:
                SaleItem.objects.create(
                    sale=sale, product=product, quantity=qty,
                    unit_price=product.current_price, unit_cost=product.cost_price,
                )
                product.stock_quantity -= qty
                product.save(update_fields=["stock_quantity"])
                StockMovement.objects.create(
                    product=product, quantity_change=-qty, reason=StockMovement.REASON_SALE,
                    note=f"Sale #{sale.id}", created_by=request.user,
                )
            messages.success(request, f"Sale #{sale.id} recorded — total {sale.total_amount}.")
            return redirect("sales:sale_detail", pk=sale.id)
    else:
        form = NewSaleForm()
    return render(request, "sales/pos.html", {"form": form, "products": products, "categories": categories})


@staff_required
def sale_list(request):
    sales = Sale.objects.select_related("cashier", "customer").prefetch_related("items")
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.is_sales_agent and not request.user.is_superuser:
        sales = sales.filter(cashier=request.user)
    sales = sales[:200]
    return render(request, "sales/sale_list.html", {"sales": sales})


@staff_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, "sales/sale_detail.html", {"sale": sale})


@manager_required
def sales_report(request):
    today = timezone.localdate()
    period = request.GET.get("period", "30")
    try:
        days = int(period)
    except ValueError:
        days = 30
    start_date = today - timedelta(days=days)

    items = SaleItem.objects.filter(sale__created_at__date__gte=start_date)

    daily = (
        items.annotate(day=TruncDate("sale__created_at"))
        .values("day")
        .annotate(
            revenue=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()),
            profit=Sum(F("unit_price") * F("quantity") - F("unit_cost") * F("quantity"), output_field=DecimalField()),
        )
        .order_by("day")
    )

    top_products = (
        items.values("product__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()))
        .order_by("-revenue")[:10]
    )

    total_revenue = items.aggregate(total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()))["total"] or 0
    total_profit = items.aggregate(
        total=Sum(F("unit_price") * F("quantity") - F("unit_cost") * F("quantity"), output_field=DecimalField())
    )["total"] or 0
    total_units = items.aggregate(total=Sum("quantity"))["total"] or 0

    chart_labels = [d["day"].strftime("%b %d") for d in daily]
    chart_revenue = [float(d["revenue"] or 0) for d in daily]

    payment_breakdown = (
        Sale.objects.filter(created_at__date__gte=start_date)
        .values("payment_method")
        .annotate(count=Sum("items__quantity"))
    )

    context = {
        "days": days,
        "start_date": start_date,
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_units": total_units,
        "top_products": top_products,
        "chart_labels": json.dumps(chart_labels),
        "chart_revenue": json.dumps(chart_revenue),
        "payment_breakdown": payment_breakdown,
    }
    return render(request, "sales/report.html", context)
