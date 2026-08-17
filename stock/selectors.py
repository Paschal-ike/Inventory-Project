from decimal import Decimal

from django.db.models import Case, DecimalField, F, QuerySet, Sum, When

from items.models import Item
from stock.models import StockTransaction
from warehouses.models import Store

_SIGNED_QUANTITY = Case(
    When(transaction_type__in=StockTransaction.IN_TYPES, then=F("quantity")),
    default=-F("quantity"),
    output_field=DecimalField(max_digits=14, decimal_places=3),
)


def balance_for_store(store: Store):
    """On-hand quantity per item at this store — IN minus OUT, computed straight
    off the ledger rather than a cached running total, so it's never out of sync."""
    return (
        StockTransaction.objects.filter(store=store)
        .values("item_id", "item__sku", "item__name", "item__unit_of_measure")
        .annotate(quantity_on_hand=Sum(_SIGNED_QUANTITY))
        .filter(quantity_on_hand__gt=0)
        .order_by("item__sku")
    )


def balance_for_store_item(store: Store, item: Item) -> Decimal:
    result = StockTransaction.objects.filter(store=store, item=item).aggregate(total=Sum(_SIGNED_QUANTITY))
    return result["total"] or Decimal("0")


def store_balances_for_project(project):
    return (
        StockTransaction.objects.filter(store__project=project)
        .values("store_id", "store__code", "store__name", "item__sku", "item__name")
        .annotate(quantity_on_hand=Sum(_SIGNED_QUANTITY))
        .filter(quantity_on_hand__gt=0)
        .order_by("store__code", "item__sku")
    )


def transactions_for_equipment(equipment) -> QuerySet[StockTransaction]:
    return equipment.stock_transactions.select_related("item", "cost_code", "work_order").order_by("-created_at")


def fuel_transactions_for_equipment(equipment) -> QuerySet[StockTransaction]:
    return transactions_for_equipment(equipment).filter(item__category="fuel", transaction_type=StockTransaction.Type.ISSUE)


def recent_transactions_for_store(store: Store, limit: int = 100) -> QuerySet[StockTransaction]:
    return (
        StockTransaction.objects.filter(store=store)
        .select_related("item", "cost_code", "equipment", "created_by")
        .order_by("-created_at")[:limit]
    )
