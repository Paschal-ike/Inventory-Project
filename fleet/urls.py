from django.urls import path

from fleet import views

app_name = "fleet"

urlpatterns = [
    path("", views.equipment_list, name="equipment_list"),
    path("new/", views.equipment_create, name="equipment_create"),
    path("<int:pk>/", views.equipment_detail, name="equipment_detail"),
    path("<int:pk>/work-orders/new/", views.work_order_create, name="work_order_create"),
    path("work-orders/<int:pk>/close/", views.work_order_close, name="work_order_close"),
]
