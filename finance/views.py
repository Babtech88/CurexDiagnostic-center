import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import staff_required, manager_required
from sales.models import Sale, SaleItem
from .forms import ExpenseForm
from .models import Expense


@staff_required
def expense_list(request):
    expenses = Expense.objects.select_related("recorded_by").all()
    category = request.GET.get("category", "")
    if category:
        expenses = expenses.filter(category=category)
    total = sum((e.amount for e in expenses), start=0)
    return render(request, "finance/expense_list.html", {
        "expenses": expenses, "category": category, "total": total,
        "categories": Expense.CATEGORY_CHOICES,
    })


@staff_required
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user
            expense.save()
            messages.success(request, "Expense recorded.")
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm(initial={"expense_date": timezone.localdate()})
    return render(request, "finance/expense_form.html", {"form": form, "title": "Record Expense"})


@staff_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated.")
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "finance/expense_form.html", {"form": form, "title": "Edit Expense"})


@manager_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted.")
    return redirect("finance:expense_list")


@manager_required
def financial_summary(request):
    today = timezone.localdate()
    period = request.GET.get("period", "30")
    try:
        days = int(period)
    except ValueError:
        days = 30
    start_date = today - timedelta(days=days)

    # --- Income (from completed sales/bookings) ---
    items = SaleItem.objects.filter(sale__created_at__date__gte=start_date)
    total_income = items.aggregate(
        total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
    )["total"] or 0
    total_cost_of_tests = items.aggregate(
        total=Sum(F("unit_cost") * F("quantity"), output_field=DecimalField())
    )["total"] or 0

    daily_income = (
        items.annotate(day=TruncDate("sale__created_at"))
        .values("day")
        .annotate(total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField()))
        .order_by("day")
    )
    income_by_day = {d["day"]: float(d["total"] or 0) for d in daily_income}

    # --- Expenditure ---
    expenses = Expense.objects.filter(expense_date__gte=start_date)
    total_expenditure = expenses.aggregate(total=Sum("amount"))["total"] or 0

    daily_expense = (
        expenses.values("expense_date")
        .annotate(total=Sum("amount"))
        .order_by("expense_date")
    )
    expense_by_day = {d["expense_date"]: float(d["total"] or 0) for d in daily_expense}

    expense_by_category = (
        expenses.values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    category_labels = dict(Expense.CATEGORY_CHOICES)
    expense_breakdown = [
        {"label": category_labels.get(e["category"], e["category"]), "total": e["total"]}
        for e in expense_by_category
    ]

    # --- Build a unified day axis for the chart ---
    all_days = sorted(set(income_by_day) | set(expense_by_day))
    chart_labels = [d.strftime("%b %d") for d in all_days]
    chart_income = [income_by_day.get(d, 0) for d in all_days]
    chart_expense = [expense_by_day.get(d, 0) for d in all_days]

    net_balance = total_income - total_expenditure
    gross_profit = total_income - total_cost_of_tests

    context = {
        "days": days,
        "start_date": start_date,
        "total_income": total_income,
        "total_expenditure": total_expenditure,
        "net_balance": net_balance,
        "gross_profit": gross_profit,
        "total_cost_of_tests": total_cost_of_tests,
        "expense_breakdown": expense_breakdown,
        "chart_labels": json.dumps(chart_labels),
        "chart_income": json.dumps(chart_income),
        "chart_expense": json.dumps(chart_expense),
    }
    return render(request, "finance/summary.html", context)
