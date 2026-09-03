from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import staff_required
from .forms import CustomerForm
from .models import Customer


@staff_required
def customer_list(request):
    customers = Customer.objects.all()
    query = request.GET.get("q", "")
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone_number__icontains=query))
    return render(request, "customers/customer_list.html", {"customers": customers, "query": query})


@staff_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.all().prefetch_related("items")
    whatsapp_orders = customer.whatsapp_orders.all()
    return render(request, "customers/customer_detail.html", {
        "customer": customer, "sales": sales, "whatsapp_orders": whatsapp_orders,
    })


@staff_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added.")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm()
    return render(request, "customers/customer_form.html", {"form": form, "title": "Add Customer"})


@staff_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated.")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customers/customer_form.html", {"form": form, "title": f"Edit {customer.name}"})


@staff_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted.")
        return redirect("customers:customer_list")
    return render(request, "customers/customer_confirm_delete.html", {"customer": customer})
