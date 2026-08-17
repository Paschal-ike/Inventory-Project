from django.db.models import QuerySet

from procurement.models import PurchaseOrder, Supplier


def active_suppliers() -> QuerySet[Supplier]:
    return Supplier.objects.filter(is_active=True)


def open_purchase_orders() -> QuerySet[PurchaseOrder]:
    return PurchaseOrder.objects.exclude(
        status__in=[PurchaseOrder.Status.RECEIVED, PurchaseOrder.Status.CANCELLED]
    ).select_related("supplier", "store")
