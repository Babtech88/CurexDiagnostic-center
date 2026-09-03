from datetime import timedelta

from django.db.models import Sum, F, DecimalField
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import StaffProfile
from accounts.permissions import staff_required, admin_required, role_required
from customers.models import Customer
from inventory.models import Product
from orders.models import WhatsAppOrder, DeliveryRequest
from results.models import TestResult
from sales.models import Sale, SaleItem
from whatsapp_bot.models import Appointment, WhatsAppContact


def _workspace(user):
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "staff_profile", None)
    role = getattr(profile, "role", None)
    if role in (StaffProfile.ROLE_ADMIN,): return "admin"
    if role in (StaffProfile.ROLE_SALES_MANAGER, StaffProfile.ROLE_SALES_AGENT): return "sales"
    if role in (StaffProfile.ROLE_MANAGER, StaffProfile.ROLE_LAB_TECH): return "lab"
    if role == StaffProfile.ROLE_DELIVERY: return "collector"
    return "admin"

@staff_required
def home(request):
    workspace = _workspace(request.user)
    return redirect({
        "admin": "dashboard:admin_home",
        "sales": "dashboard:sales_home",
        "lab": "dashboard:lab_home",
        "collector": "dashboard:collector_home",
    }[workspace])

@admin_required
def admin_home(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    items_today = SaleItem.objects.filter(sale__created_at__date=today)
    items_week = SaleItem.objects.filter(sale__created_at__date__gte=week_ago)
    revenue_today = items_today.aggregate(total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()))["total"] or 0
    revenue_week = items_week.aggregate(total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()))["total"] or 0
    products = Product.objects.filter(is_active=True)
    staff = StaffProfile.objects.select_related("user").filter(is_active_staff=True)
    context = {
        "workspace":"admin", "revenue_today":revenue_today, "revenue_week":revenue_week,
        "sales_today":Sale.objects.filter(created_at__date=today).count(),
        "patients":Customer.objects.count(), "products":products.count(),
        "staff_count":staff.count(),
        "pending_orders":WhatsAppOrder.objects.filter(status=WhatsAppOrder.STATUS_PENDING).count(),
        "pending_collections":DeliveryRequest.objects.filter(status=DeliveryRequest.STATUS_PENDING).count(),
        "pending_appointments":Appointment.objects.filter(status=Appointment.STATUS_PENDING).count(),
        "results_today":TestResult.objects.filter(uploaded_at__date=today).count(),
        "low_stock":sum(1 for x in products if x.is_low_stock),
        "recent_sales":Sale.objects.select_related("cashier","customer").order_by("-created_at")[:6],
        "recent_orders":WhatsAppOrder.objects.order_by("-created_at")[:5],
    }
    return render(request, "dashboard/admin_home.html", context)

@role_required("sales_manager", "sales_agent")
def sales_home(request):
    today=timezone.localdate(); week=today-timedelta(days=7)
    profile=getattr(request.user,"staff_profile",None)
    mine=bool(profile and profile.role==StaffProfile.ROLE_SALES_AGENT)
    sale_q={"cashier":request.user} if mine else {}
    item_q={"sale__cashier":request.user} if mine else {}
    today_items=SaleItem.objects.filter(sale__created_at__date=today, **item_q)
    week_items=SaleItem.objects.filter(sale__created_at__date__gte=week, **item_q)
    total_today=today_items.aggregate(total=Sum(F("unit_price")*F("quantity"),output_field=DecimalField()))["total"] or 0
    total_week=week_items.aggregate(total=Sum(F("unit_price")*F("quantity"),output_field=DecimalField()))["total"] or 0
    chats=WhatsAppContact.objects.filter(assigned_agent=request.user) if mine else WhatsAppContact.objects.all()
    return render(request,"dashboard/sales_home.html",{
        "workspace":"sales","is_manager":not mine,"today_revenue":total_today,"week_revenue":total_week,
        "today_sales":Sale.objects.filter(created_at__date=today,**sale_q).count(),
        "customers":Customer.objects.count() if not mine else Sale.objects.filter(**sale_q).exclude(customer__isnull=True).values("customer").distinct().count(),
        "open_chats":chats.count(),"human_chats":chats.filter(needs_human=True).count(),
        "recent_sales":Sale.objects.select_related("customer","cashier").filter(**sale_q).order_by("-created_at")[:8],
    })

@role_required("manager", "lab_tech")
def lab_home(request):
    today=timezone.localdate()
    profile=getattr(request.user,"staff_profile",None)
    is_manager=bool(profile and profile.role==StaffProfile.ROLE_MANAGER)
    results=TestResult.objects.select_related("customer","product")
    if not is_manager:
        results=results.filter(uploaded_by=request.user)
    return render(request,"dashboard/lab_home.html",{
        "workspace":"lab","is_manager":is_manager,
        "total_results":results.count(), "today_results":results.filter(uploaded_at__date=today).count(),
        "unreleased":results.filter(is_released=False).count(),
        "collections_waiting":DeliveryRequest.objects.filter(status__in=[DeliveryRequest.STATUS_PENDING,DeliveryRequest.STATUS_DISPATCHED]).count(),
        "recent_results":results.order_by("-uploaded_at")[:8],
    })

@role_required("delivery")
def collector_home(request):
    today=timezone.localdate()
    deliveries=DeliveryRequest.objects.select_related("whatsapp_order","sale").filter(assigned_rider=request.user)
    return render(request,"dashboard/collector_home.html",{
        "workspace":"collector","today":today,
        "assigned":deliveries.count(),
        "pending":deliveries.filter(status=DeliveryRequest.STATUS_PENDING).count(),
        "in_progress":deliveries.filter(status=DeliveryRequest.STATUS_DISPATCHED).count(),
        "completed":deliveries.filter(status=DeliveryRequest.STATUS_DELIVERED).count(),
        "deliveries":deliveries.order_by("scheduled_date","-created_at")[:12],
    })
