from django.db.models import QuerySet

from fleet.models import Equipment, WorkOrder


def active_equipment() -> QuerySet[Equipment]:
    return Equipment.objects.filter(status=Equipment.Status.ACTIVE).select_related("home_store")


def open_work_orders_for(equipment: Equipment) -> QuerySet[WorkOrder]:
    return equipment.work_orders.exclude(status=WorkOrder.Status.CLOSED)


def open_work_orders() -> QuerySet[WorkOrder]:
    return WorkOrder.objects.exclude(status=WorkOrder.Status.CLOSED).select_related("equipment", "cost_code")
