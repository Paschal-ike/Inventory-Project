from django.core.exceptions import PermissionDenied

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from items.models import Item
from items.permissions import can_manage_items


def create_item(
    *,
    sku: str,
    name: str,
    category: str,
    unit_of_measure: str,
    valuation_method: str,
    reorder_level,
    created_by: User,
) -> Item:
    if not can_manage_items(created_by):
        raise PermissionDenied("You do not have permission to create items.")
    item = Item.objects.create(
        sku=sku,
        name=name,
        category=category,
        unit_of_measure=unit_of_measure,
        valuation_method=valuation_method,
        reorder_level=reorder_level or 0,
        created_by=created_by,
    )
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.ITEM_CREATED,
        description=f"Created item {item.sku!r} — {item.name} ({item.get_category_display()})",
        target=item,
    )
    return item
