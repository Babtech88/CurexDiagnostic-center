from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "cashier", "customer", "payment_method", "source", "created_at", "total_amount")
    list_filter = ("payment_method", "source")
    inlines = [SaleItemInline]
