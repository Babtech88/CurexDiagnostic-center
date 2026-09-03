from django.urls import path
from . import views
app_name = "dashboard"
urlpatterns = [
 path("", views.home, name="home"),
 path("admin/", views.admin_home, name="admin_home"),
 path("sales/", views.sales_home, name="sales_home"),
 path("lab/", views.lab_home, name="lab_home"),
 path("collector/", views.collector_home, name="collector_home"),
]
