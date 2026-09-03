from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # Public cart / WhatsApp checkout
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("cart/checkout/", views.cart_checkout, name="cart_checkout"),
    path("whatsapp/<int:pk>/redirect/", views.whatsapp_redirect, name="whatsapp_redirect"),

    # Staff: WhatsApp orders
    path("whatsapp-orders/", views.whatsapp_order_list, name="whatsapp_order_list"),
    path("whatsapp-orders/<int:pk>/", views.whatsapp_order_detail, name="whatsapp_order_detail"),
    path("whatsapp-orders/<int:pk>/status/<str:status>/", views.whatsapp_order_set_status, name="whatsapp_order_set_status"),
    path("whatsapp-orders/<int:pk>/convert/", views.whatsapp_order_convert_to_sale, name="whatsapp_order_convert"),

    # Staff: deliveries
    path("deliveries/", views.delivery_list, name="delivery_list"),
    path("deliveries/<int:pk>/edit/", views.delivery_update, name="delivery_update"),
]
