from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db import transaction

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from procurement.models import PurchaseOrder, PurchaseOrderLine, Supplier
from procurement.permissions import can_create_purchase_order, can_manage_suppliers
from stock.services import receive_purchase
from warehouses.models import Store


def create_supplier(
    *, name: str, contact_name: str, contact_phone: str, contact_email: str, country: str, created_by: User
) -> Supplier:
    if not can_manage_suppliers(created_by):
        raise PermissionDenied("You do not have permission to create suppliers.")
    return Supplier.objects.create(
        name=name,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        country=country,
        created_by=created_by,
    )


@transaction.atomic
def create_purchase_order(
    *,
    reference: str,
    supplier: Supplier,
    store: Store,
    currency: str,
    lines: list[dict],
    created_by: User,
) -> PurchaseOrder:
    """`lines` is a list of {"item": Item, "quantity_ordered": Decimal, "unit_price": Decimal,
    "cost_code": CostCode | None}."""
    if not can_create_purchase_order(created_by):
        raise PermissionDenied("You do not have permission to create purchase orders.")
    po = PurchaseOrder.objects.create(
        reference=reference,
        supplier=supplier,
        store=store,
        currency=currency,
        status=PurchaseOrder.Status.ORDERED,
        created_by=created_by,
    )
    PurchaseOrderLine.objects.bulk_create(
        [
            PurchaseOrderLine(
                purchase_order=po,
                item=line["item"],
                quantity_ordered=line["quantity_ordered"],
                unit_price=line["unit_price"],
                cost_code=line.get("cost_code"),
            )
            for line in lines
        ]
    )
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.PURCHASE_ORDER_CREATED,
        description=f"Created {po.reference} with {supplier.name} ({len(lines)} line(s))",
        target=po,
    )
    return po


@transaction.atomic
def receive_purchase_order_line(*, line: PurchaseOrderLine, quantity: Decimal, actor: User) -> None:
    """Posts the GRN through stock.services.receive_purchase (which owns the store/role
    permission check) then reconciles the line and parent PO status."""
    receive_purchase(
        store=line.purchase_order.store,
        item=line.item,
        quantity=quantity,
        unit_cost=line.unit_price,
        reference=line.purchase_order.reference,
        actor=actor,
    )
    line.quantity_received += quantity
    line.save(update_fields=["quantity_received", "updated_at"])

    po = line.purchase_order
    lines = po.lines.all()
    if all(l.quantity_received >= l.quantity_ordered for l in lines):
        po.status = PurchaseOrder.Status.RECEIVED
    elif any(l.quantity_received > 0 for l in lines):
        po.status = PurchaseOrder.Status.PARTIALLY_RECEIVED
    po.save(update_fields=["status", "updated_at"])
