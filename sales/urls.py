from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("new/", views.pos_new_sale, name="pos_new_sale"),
    path("", views.sale_list, name="sale_list"),
    path("report/", views.sales_report, name="report"),
    path("<int:pk>/", views.sale_detail, name="sale_detail"),
]
