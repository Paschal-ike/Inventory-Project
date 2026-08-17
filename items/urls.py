from django.urls import path

from items import views

app_name = "items"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("new/", views.item_create, name="item_create"),
]
