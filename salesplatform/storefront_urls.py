from django.urls import path
from inventory import views as inventory_views

app_name = "storefront"

urlpatterns = [
    path("", inventory_views.storefront_home, name="home"),
    path("catalog/", inventory_views.storefront_catalog, name="catalog"),
    path("product/<int:pk>/", inventory_views.storefront_product_detail, name="product_detail"),
]
