from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from fleet.models import Equipment, WorkOrder
from fleet.permissions import can_close_work_order, can_manage_equipment, can_open_work_order
from warehouses.models import Store


def create_equipment(
    *,
    asset_tag: str,
    name: str,
    equipment_class: str,
    home_store: Store,
    meter_type: str,
    fuel_type: str,
    created_by: User,
) -> Equipment:
    if not can_manage_equipment(created_by):
        raise PermissionDenied("You do not have permission to register equipment.")
    equipment = Equipment.objects.create(
        asset_tag=asset_tag,
        name=name,
        equipment_class=equipment_class,
        home_store=home_store,
        meter_type=meter_type,
        fuel_type=fuel_type,
        created_by=created_by,
    )
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.EQUIPMENT_CREATED,
        description=f"Registered equipment {equipment.asset_tag!r} — {equipment.name}",
        target=equipment,
    )
    return equipment


def open_work_order(
    *, equipment: Equipment, work_type: str, description: str, cost_code, opened_by: User
) -> WorkOrder:
    if not can_open_work_order(opened_by):
        raise PermissionDenied("You do not have permission to open work orders.")
    work_order = WorkOrder.objects.create(
        equipment=equipment,
        work_type=work_type,
        description=description,
        cost_code=cost_code,
        opened_by=opened_by,
    )
    log_event(
        actor=opened_by,
        action=AuditLogEntry.Action.WORK_ORDER_OPENED,
        description=f"Opened {work_order} for {equipment.asset_tag}",
        target=work_order,
        project=cost_code.project if cost_code else None,
    )
    return work_order


def close_work_order(*, work_order: WorkOrder, actor: User) -> WorkOrder:
    if not can_close_work_order(actor):
        raise PermissionDenied("You do not have permission to close work orders.")
    work_order.status = WorkOrder.Status.CLOSED
    work_order.closed_at = timezone.now()
    work_order.save(update_fields=["status", "closed_at", "updated_at"])
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.WORK_ORDER_CLOSED,
        description=f"Closed {work_order}",
        target=work_order,
    )
    return work_order


@transaction.atomic
def record_meter_reading(*, equipment: Equipment, reading, actor: User) -> Equipment:
    """A meter can only go forward — a lower reading than what's on file usually means
    the wrong unit was selected, not that the clock ran backwards."""
    if reading < equipment.current_meter_reading:
        raise ValidationError(
            f"New reading ({reading}) is behind the current reading ({equipment.current_meter_reading}) "
            f"for {equipment.asset_tag}. Check you picked the right unit."
        )
    equipment.current_meter_reading = reading
    equipment.save(update_fields=["current_meter_reading", "updated_at"])
    return equipment
