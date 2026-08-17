from django.core.exceptions import PermissionDenied
from django.db import transaction

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from warehouses.models import Quarry, Store, StoreAssignment
from warehouses.permissions import can_manage_store, can_manage_store_assignments


def create_store(
    *,
    name: str,
    code: str,
    store_type: str,
    country: str,
    state_or_region: str,
    project=None,
    parent: Store | None = None,
    created_by: User,
) -> Store:
    if not can_manage_store(created_by):
        raise PermissionDenied("You do not have permission to create stores.")
    store = Store.objects.create(
        name=name,
        code=code,
        store_type=store_type,
        country=country,
        state_or_region=state_or_region,
        project=project,
        parent=parent,
        created_by=created_by,
    )
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.STORE_CREATED,
        description=f"Created store {store.code!r} ({store.get_store_type_display()})",
        target=store,
        project=project,
    )
    return store


@transaction.atomic
def create_quarry(
    *,
    name: str,
    stockyard_code: str,
    country: str,
    location: str,
    licensed_material_types: str,
    created_by: User,
) -> Quarry:
    if not can_manage_store(created_by):
        raise PermissionDenied("You do not have permission to create a quarry.")
    stockyard = Store.objects.create(
        name=f"{name} Stockyard",
        code=stockyard_code,
        store_type=Store.StoreType.QUARRY_STOCKYARD,
        country=country,
        state_or_region=location,
        created_by=created_by,
    )
    return Quarry.objects.create(
        name=name,
        stockyard=stockyard,
        country=country,
        location=location,
        licensed_material_types=licensed_material_types,
        created_by=created_by,
    )


def assign_user_to_store(*, store: Store, user: User, actor: User) -> StoreAssignment:
    if not can_manage_store_assignments(actor, store):
        raise PermissionDenied("You do not have permission to manage assignments on this store.")
    assignment, _ = StoreAssignment.objects.get_or_create(store=store, user=user, defaults={"added_by": actor})
    return assignment


def unassign_user_from_store(*, store: Store, user: User, actor: User) -> None:
    if not can_manage_store_assignments(actor, store):
        raise PermissionDenied("You do not have permission to manage assignments on this store.")
    StoreAssignment.objects.filter(store=store, user=user).delete()
