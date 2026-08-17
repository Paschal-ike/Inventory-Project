from django.urls import path

from stock import views

app_name = "stock"

urlpatterns = [
    path("stores/<int:store_pk>/", views.store_ledger, name="store_ledger"),
    path("stores/<int:store_pk>/issue/", views.issue_form, name="issue_form"),
    path("stores/<int:store_pk>/transfer/", views.transfer_form, name="transfer_form"),
    path("stores/<int:store_pk>/receive/", views.receive_form, name="receive_form"),
    path("stores/<int:store_pk>/adjust/", views.adjust_form, name="adjust_form"),
    path("quarries/<int:quarry_pk>/log-production/", views.quarry_receipt_form, name="quarry_receipt_form"),
]
