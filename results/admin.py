from django.contrib import admin
from .models import TestResult


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "access_code", "is_released", "uploaded_by", "uploaded_at")
    list_filter = ("is_released",)
    search_fields = ("customer__name", "customer__phone_number", "access_code", "product__name")
    readonly_fields = ("access_code",)
