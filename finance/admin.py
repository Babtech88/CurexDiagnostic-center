from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "category", "amount", "expense_date", "recorded_by")
    list_filter = ("category",)
    search_fields = ("description", "notes")
