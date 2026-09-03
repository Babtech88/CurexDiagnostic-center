from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import staff_required, manager_required
from .forms import EquipmentForm, QuickStatusForm, MaintenanceLogForm
from .models import Equipment


@staff_required
def equipment_list(request):
    equipment = Equipment.objects.select_related("assigned_technician").all()
    status = request.GET.get("status", "")
    if status:
        equipment = equipment.filter(status=status)

    operational_count = Equipment.objects.filter(status=Equipment.STATUS_OPERATIONAL).count()
    attention_count = Equipment.objects.exclude(status=Equipment.STATUS_OPERATIONAL).count()
    overdue_count = sum(1 for e in Equipment.objects.all() if e.is_overdue_for_maintenance)

    return render(request, "equipment/equipment_list.html", {
        "equipment": equipment, "status": status,
        "operational_count": operational_count, "attention_count": attention_count,
        "overdue_count": overdue_count, "status_choices": Equipment.STATUS_CHOICES,
    })


@staff_required
def equipment_detail(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    logs = item.maintenance_logs.select_related("performed_by").all()

    if request.method == "POST":
        log_form = MaintenanceLogForm(request.POST)
        if log_form.is_valid():
            log = log_form.save(commit=False)
            log.equipment = item
            log.performed_by = request.user
            log.save()
            item.status = log.status_after
            if log.status_after == Equipment.STATUS_OPERATIONAL:
                item.last_serviced_date = log.log_date
            item.save(update_fields=["status", "last_serviced_date"])
            messages.success(request, "Maintenance log added and status updated.")
            return redirect("equipment:equipment_detail", pk=pk)
    else:
        log_form = MaintenanceLogForm(initial={"status_after": item.status})

    return render(request, "equipment/equipment_detail.html", {
        "item": item, "logs": logs, "log_form": log_form,
    })


@manager_required
def equipment_create(request):
    if request.method == "POST":
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipment added.")
            return redirect("equipment:equipment_list")
    else:
        form = EquipmentForm()
    return render(request, "equipment/equipment_form.html", {"form": form, "title": "Add Equipment"})


@manager_required
def equipment_edit(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        form = EquipmentForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipment updated.")
            return redirect("equipment:equipment_detail", pk=pk)
    else:
        form = EquipmentForm(instance=item)
    return render(request, "equipment/equipment_form.html", {"form": form, "title": f"Edit {item.name}"})


@staff_required
def equipment_quick_status(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        form = QuickStatusForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"{item.name} status updated to {item.get_status_display()}.")
    return redirect("equipment:equipment_list")


@manager_required
def equipment_delete(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Equipment removed.")
        return redirect("equipment:equipment_list")
    return render(request, "equipment/equipment_confirm_delete.html", {"item": item})
