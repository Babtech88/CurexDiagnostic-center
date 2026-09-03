from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("add/", views.product_create, name="product_create"),
    path("alerts/", views.alerts_view, name="alerts"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("<int:pk>/restock/", views.product_restock, name="product_restock"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/<int:pk>/delete/", views.supplier_delete, name="supplier_delete"),

    path("promotions/", views.promotion_list, name="promotion_list"),
    path("promotions/add/", views.promotion_create, name="promotion_create"),
    path("promotions/<int:pk>/edit/", views.promotion_edit, name="promotion_edit"),
    path("promotions/<int:pk>/delete/", views.promotion_delete, name="promotion_delete"),
]
