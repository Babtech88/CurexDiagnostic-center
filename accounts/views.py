from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum, F, DecimalField
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import StaffCreateForm, StaffEditForm
from .models import StaffProfile
from .permissions import admin_required, manager_required, sales_manager_required, sales_staff_required
from sales.models import Sale, SaleItem
from whatsapp_bot.models import WhatsAppContact


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        # First use Django's normal authentication. If the user typed a different
        # username case or their account email, resolve the account safely and
        # authenticate using its canonical username.
        user = authenticate(request, username=identifier, password=password)
        if user is None and identifier:
            candidate = User.objects.filter(username__iexact=identifier).first()
            if candidate is None and "@" in identifier:
                candidate = User.objects.filter(email__iexact=identifier).first()
            if candidate is not None:
                user = authenticate(request, username=candidate.username, password=password)
        if user is not None:
            profile = getattr(user, "staff_profile", None)
            if not user.is_active:
                messages.error(request, "This account is inactive. Please contact an administrator.")
            elif not user.is_superuser and profile is None:
                messages.error(request, "Your account is not configured for a staff workspace.")
            elif not user.is_superuser and not profile.is_active_staff:
                messages.error(request, "Your staff account is inactive. Please contact an administrator.")
            else:
                login(request, user)
                return redirect("dashboard:home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")



def sales_admin_login(request):
    """Dedicated login for Sales Administrators/Sales Managers; does not use Django /admin/."""
    if request.user.is_authenticated:
        profile = getattr(request.user, "staff_profile", None)
        if request.user.is_superuser or (profile and profile.role in {
            StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_MANAGER, StaffProfile.ROLE_SALES_MANAGER
        }):
            return redirect("sales:report")
        logout(request)

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        profile = getattr(user, "staff_profile", None) if user else None
        allowed = bool(
            user and (
                user.is_superuser or (
                    profile and profile.is_active_staff and profile.role in {
                        StaffProfile.ROLE_ADMIN,
                        StaffProfile.ROLE_MANAGER,
                        StaffProfile.ROLE_SALES_MANAGER,
                    }
                )
            )
        )
        if allowed:
            login(request, user)
            return redirect("sales:report")
        messages.error(request, "Invalid Sales Admin credentials or this account does not have Sales Admin access.")

    return render(request, "accounts/sales_admin_login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@manager_required
def staff_list(request):
    staff = StaffProfile.objects.select_related("user").all()
    return render(request, "accounts/staff_list.html", {"staff": staff})


@sales_manager_required
def staff_create(request):
    is_admin = bool(request.user.is_superuser or getattr(getattr(request.user, "staff_profile", None), "is_admin", False))
    allowed_roles = None if is_admin else [StaffProfile.ROLE_SALES_AGENT]
    if request.method == "POST":
        form = StaffCreateForm(request.POST, allowed_roles=allowed_roles)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff member added. They can now sign in with their own account.")
            return redirect("accounts:staff_list")
    else:
        form = StaffCreateForm(allowed_roles=allowed_roles)
    return render(request, "accounts/staff_form.html", {"form": form, "title": "Add Sales Agent" if not is_admin else "Add Staff Member"})


@admin_required
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == "POST":
        form = StaffEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff record updated.")
            return redirect("accounts:staff_list")
    else:
        form = StaffEditForm(instance=profile)
    return render(request, "accounts/staff_form.html", {"form": form, "title": f"Edit {profile.user.username}"})


@admin_required
def staff_delete(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == "POST":
        user = profile.user
        user.delete()
        messages.success(request, "Staff member removed.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_confirm_delete.html", {"profile": profile})


@sales_staff_required
def sales_team(request):
    """Sales-manager view of agents, their WhatsApp workload and recorded sales."""
    profile = getattr(request.user, "staff_profile", None)
    today = timezone.localdate()
    month_start = today.replace(day=1)

    team_qs = StaffProfile.objects.filter(
        role__in=[StaffProfile.ROLE_SALES_MANAGER, StaffProfile.ROLE_SALES_AGENT]
    ).select_related("user")

    if profile and profile.is_sales_agent and not request.user.is_superuser:
        team_qs = team_qs.filter(user=request.user)

    rows = []
    for member in team_qs:
        user = member.user
        chats = WhatsAppContact.objects.filter(assigned_agent=user)
        month_items = SaleItem.objects.filter(
            sale__cashier=user, sale__created_at__date__gte=month_start
        )
        revenue = month_items.aggregate(
            total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
        )["total"] or 0
        rows.append({
            "profile": member,
            "open_chats": chats.count(),
            "human_chats": chats.filter(needs_human=True).count(),
            "sales_count": Sale.objects.filter(cashier=user, created_at__date__gte=month_start).count(),
            "revenue": revenue,
        })

    return render(request, "accounts/sales_team.html", {
        "rows": rows,
        "month_start": month_start,
        "is_manager": bool(request.user.is_superuser or (profile and profile.is_sales_manager_or_admin)),
    })
