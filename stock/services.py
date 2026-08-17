from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from fleet.models import Equipment, WorkOrder
from fleet.services import record_meter_reading
from items.models import Item
from projects.models import CostCode
from projects.permissions import can_use_cost_code
from stock.models import StockTransaction
from stock.permissions import can_adjust, can_issue_from, can_log_quarry_receipt, can_receive_stock, can_transfer_stock
from stock.selectors import balance_for_store_item
from warehouses.models import Quarry, Store


def _weighted_average_unit_cost(store: Store, item: Item) -> Decimal | None:
    """
    A simplified snapshot WAC — averages unit_cost across every inbound
    transaction on record for this store/item, weighted by quantity. This is
    not a true perpetual WAC (it doesn't retire cost layers as stock is
    consumed), which is fine for an MVP issue-cost estimate but should be
    replaced with a proper costing layer (FIFO or perpetual WAC) before this
    number is relied on for financial reporting.
    """
    rows = StockTransaction.objects.filter(
        store=store, item=item, transaction_type__in=StockTransaction.IN_TYPES, unit_cost__isnull=False
    ).values_list("quantity", "unit_cost")
    total_qty = sum((q for q, _ in rows), Decimal("0"))
    if total_qty == 0:
        return None
    total_value = sum((q * c for q, c in rows), Decimal("0"))
    return (total_value / total_qty).quantize(Decimal("0.01"))


@transaction.atomic
def log_quarry_production(
    *, quarry: Quarry, item: Item, quantity: Decimal, unit_cost: Decimal, reference: str, actor: User
) -> StockTransaction:
    if not can_log_quarry_receipt(actor, quarry.stockyard):
        raise PermissionDenied("You do not have permission to log production for this quarry.")
    txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.QUARRY_RECEIPT,
        item=item,
        store=quarry.stockyard,
        quantity=quantity,
        unit_cost=unit_cost,
        reference=reference,
        created_by=actor,
    )
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.QUARRY_PRODUCTION_LOGGED,
        description=f"{quarry.name}: +{quantity} {item.unit_of_measure} {item.sku}",
        target=txn,
    )
    return txn


@transaction.atomic
def receive_purchase(
    *, store: Store, item: Item, quantity: Decimal, unit_cost: Decimal, reference: str, actor: User
) -> StockTransaction:
    if not can_receive_stock(actor, store):
        raise PermissionDenied("You do not have permission to receive stock into this store.")
    txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.PURCHASE_RECEIPT,
        item=item,
        store=store,
        quantity=quantity,
        unit_cost=unit_cost,
        reference=reference,
        created_by=actor,
    )
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.PURCHASE_RECEIPT,
        description=f"{store.code}: +{quantity} {item.unit_of_measure} {item.sku} (ref {reference or '—'})",
        target=txn,
    )
    return txn


@transaction.atomic
def transfer_stock(
    *,
    source_store: Store,
    destination_store: Store,
    item: Item,
    quantity: Decimal,
    reference: str,
    actor: User,
) -> tuple[StockTransaction, StockTransaction]:
    """
    Single-step transfer: both legs post atomically under one actor's
    authority over the source store. A two-step "dispatch, then confirm
    receipt at the destination" flow is a reasonable Phase-2 refinement for
    catching in-transit loss, but isn't needed to prove the core model out.
    """
    if not can_transfer_stock(actor, source_store):
        raise PermissionDenied("You do not have permission to transfer stock from this store.")
    if source_store.pk == destination_store.pk:
        raise ValidationError("Source and destination store must be different.")

    available = balance_for_store_item(source_store, item)
    if quantity > available:
        raise ValidationError(
            f"Only {available} {item.unit_of_measure} of {item.sku} available at {source_store.code}; "
            f"cannot transfer {quantity}."
        )

    unit_cost = _weighted_average_unit_cost(source_store, item)

    out_txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.TRANSFER_OUT,
        item=item,
        store=source_store,
        quantity=quantity,
        unit_cost=unit_cost,
        reference=reference,
        created_by=actor,
    )
    in_txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.TRANSFER_IN,
        item=item,
        store=destination_store,
        quantity=quantity,
        unit_cost=unit_cost,
        reference=reference,
        related_transaction=out_txn,
        created_by=actor,
    )
    out_txn.related_transaction = in_txn
    out_txn.save(update_fields=["related_transaction", "updated_at"])

    log_event(
        actor=actor,
        action=AuditLogEntry.Action.INTERNAL_TRANSFER,
        description=f"{quantity} {item.unit_of_measure} {item.sku}: {source_store.code} → {destination_store.code}",
        target=out_txn,
        project=destination_store.project,
    )
    return out_txn, in_txn


@transaction.atomic
def issue_stock(
    *,
    store: Store,
    item: Item,
    quantity: Decimal,
    actor: User,
    cost_code: CostCode | None = None,
    equipment: Equipment | None = None,
    work_order: WorkOrder | None = None,
    meter_reading: Decimal | None = None,
    reference: str = "",
) -> StockTransaction:
    if not can_issue_from(actor, store):
        raise PermissionDenied("You do not have permission to issue stock from this store.")

    # A work order set up as job-billable already knows its cost code — the
    # issuer shouldn't have to re-key it, and it should win over a blank
    # selection. An explicitly chosen cost code still overrides a work
    # order's plant-overhead default (cost_code is None on the work order).
    if cost_code is None and work_order is not None:
        cost_code = work_order.cost_code

    if cost_code is None:
        raise ValidationError(
            "This issue needs a cost code — either pick one directly, or attach it to a "
            "work order that already carries one."
        )
    if not can_use_cost_code(actor, cost_code):
        raise PermissionDenied("You do not have access to that cost code's project.")

    available = balance_for_store_item(store, item)
    if quantity > available:
        raise ValidationError(
            f"Only {available} {item.unit_of_measure} of {item.sku} available at {store.code}; "
            f"cannot issue {quantity}."
        )

    if item.is_fuel and equipment is not None:
        if meter_reading is None:
            raise ValidationError("A meter reading is required when dispensing fuel against an equipment unit.")
        record_meter_reading(equipment=equipment, reading=meter_reading, actor=actor)

    unit_cost = _weighted_average_unit_cost(store, item)

    txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.ISSUE,
        item=item,
        store=store,
        quantity=quantity,
        unit_cost=unit_cost,
        cost_code=cost_code,
        equipment=equipment,
        work_order=work_order,
        meter_reading=meter_reading,
        reference=reference,
        created_by=actor,
    )
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.STOCK_ISSUE,
        description=f"{store.code}: -{quantity} {item.unit_of_measure} {item.sku} → {cost_code.code}"
        + (f" ({equipment.asset_tag})" if equipment else ""),
        target=txn,
        project=cost_code.project,
    )
    return txn


@transaction.atomic
def return_stock(
    *, store: Store, item: Item, quantity: Decimal, actor: User, cost_code: CostCode | None = None, reference: str = ""
) -> StockTransaction:
    if not can_issue_from(actor, store):
        raise PermissionDenied("You do not have permission to receive returns at this store.")
    txn = StockTransaction.objects.create(
        transaction_type=StockTransaction.Type.RETURN,
        item=item,
        store=store,
        quantity=quantity,
        cost_code=cost_code,
        reference=reference,
        created_by=actor,
    )
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.STOCK_RETURN,
        description=f"{store.code}: +{quantity} {item.unit_of_measure} {item.sku} returned",
        target=txn,
        project=cost_code.project if cost_code else None,
    )
    return txn


@transaction.atomic
def adjust_stock(
    *,
    store: Store,
    item: Item,
    counted_quantity: Decimal,
    actor: User,
    cost_code: CostCode | None = None,
    reference: str = "",
) -> StockTransaction | None:
    """Reconciles a physical count against the ledger. A shortfall (shrinkage,
    pilferage) must land on a cost code just like an issue does — an overage
    doesn't need one, since nothing was consumed."""
    if not can_adjust(actor, store):
        raise PermissionDenied("You do not have permission to adjust stock at this store.")

    system_quantity = balance_for_store_item(store, item)
    variance = counted_quantity - system_quantity
    if variance == 0:
        return None

    if variance > 0:
        txn_type = StockTransaction.Type.ADJUSTMENT_IN
        txn_cost_code = cost_code
    else:
        txn_type = StockTransaction.Type.ADJUSTMENT_OUT
        if cost_code is None:
            raise ValidationError(
                "A shortfall against the physical count needs a cost code to charge the loss to "
                "(e.g. a stock-loss overhead code)."
            )
        txn_cost_code = cost_code

    txn = StockTransaction.objects.create(
        transaction_type=txn_type,
        item=item,
        store=store,
        quantity=abs(variance),
        cost_code=txn_cost_code,
        reference=reference,
        created_by=actor,
    )
    log_event(
        actor=actor,
        action=AuditLogEntry.Action.STOCK_ADJUSTMENT,
        description=f"{store.code}: count {counted_quantity} vs system {system_quantity} "
        f"— {'+' if variance > 0 else ''}{variance} {item.unit_of_measure} {item.sku}",
        target=txn,
        project=txn_cost_code.project if txn_cost_code else None,
    )
    return txn
