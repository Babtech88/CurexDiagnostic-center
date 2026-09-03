from django.contrib import admin
from .models import Category, Supplier, Product, Promotion, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "email")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "sku", "category", "selling_price", "stock_quantity",
        "low_stock_threshold", "expiry_date", "is_active",
    )
    list_filter = ("category", "is_active", "supplier")
    search_fields = ("name", "sku")


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "discount_percent", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    filter_horizontal = ("products",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity_change", "reason", "created_by", "created_at")
    list_filter = ("reason",)
    search_fields = ("product__name",)
