from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("admin/", views.login_view, name="admin_login"),
    path("sales-admin/login/", views.sales_admin_login, name="sales_admin_login"),
    path("logout/", views.logout_view, name="logout"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/add/", views.staff_create, name="staff_create"),
    path("staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),
    path("sales-team/", views.sales_team, name="sales_team"),
]
