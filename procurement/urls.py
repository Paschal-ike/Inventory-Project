from django.urls import path

from procurement import views

app_name = "procurement"

urlpatterns = [
    path("", views.purchase_order_list, name="purchase_order_list"),
    path("<int:pk>/", views.purchase_order_detail, name="purchase_order_detail"),
    path("lines/<int:pk>/receive/", views.receive_line, name="receive_line"),
]
