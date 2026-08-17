from django.urls import path

from warehouses import views

app_name = "warehouses"

urlpatterns = [
    path("", views.store_list, name="store_list"),
    path("new/", views.store_create, name="store_create"),
    path("<int:pk>/", views.store_detail, name="store_detail"),
]
