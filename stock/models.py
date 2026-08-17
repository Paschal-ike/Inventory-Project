from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class StockTransaction(TimeStampedModel):
    """
    The ledger — the single source of truth for "where did this unit of
    stock go and who pays for it". Append-only: corrections are reversing
    entries (an ADJUSTMENT_IN/OUT pair), never edits to a posted row, since
    this doubles as the project's material-cost record.

    Direction is baked into the transaction type itself (IN_TYPES / OUT_TYPES
    below) rather than carried as a signed quantity, so a balance query is
    just "sum of IN minus sum of OUT" with no sign bugs to worry about.
    """

    class Type(models.TextChoices):
        QUARRY_RECEIPT = "quarry_receipt", "Quarry Production Receipt"
        PURCHASE_RECEIPT = "purchase_receipt", "Purchase Receipt (GRN)"
        TRANSFER_IN = "transfer_in", "Internal Transfer In"
        TRANSFER_OUT = "transfer_out", "Internal Transfer Out"
        ISSUE = "issue", "Issue"
        RETURN = "return", "Return"
        ADJUSTMENT_IN = "adjustment_in", "Stock Count Adjustment (Increase)"
        ADJUSTMENT_OUT = "adjustment_out", "Stock Count Adjustment (Decrease)"

    IN_TYPES = {Type.QUARRY_RECEIPT, Type.PURCHASE_RECEIPT, Type.TRANSFER_IN, Type.RETURN, Type.ADJUSTMENT_IN}
    OUT_TYPES = {Type.TRANSFER_OUT, Type.ISSUE, Type.ADJUSTMENT_OUT}

    # Cost code is mandatory on any transaction that removes stock without a
    # transfer note to account for where it went — issuing to a job, and
    # a downward count adjustment (shrinkage/pilferage), both have to land
    # on something. Enforced again at the DB level below.
    COST_CODE_REQUIRED_TYPES = {Type.ISSUE, Type.ADJUSTMENT_OUT}

    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    item = models.ForeignKey("items.Item", on_delete=models.PROTECT, related_name="stock_transactions")
    store = models.ForeignKey("warehouses.Store", on_delete=models.PROTECT, related_name="stock_transactions")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, help_text="Cost per unit at time of transaction."
    )
    cost_code = models.ForeignKey(
        "projects.CostCode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )
    equipment = models.ForeignKey(
        "fleet.Equipment",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_transactions",
        help_text="Set when this is a fuel or spare-part issue against a specific unit.",
    )
    work_order = models.ForeignKey(
        "fleet.WorkOrder",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )
    meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Equipment hour-meter/odometer reading at time of a fuel dispense.",
    )
    related_transaction = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        help_text="Links a TRANSFER_OUT row to its paired TRANSFER_IN row at the destination store.",
    )
    reference = models.CharField(
        max_length=64, blank=True, help_text="Transfer note / GRN / stock-take reference number."
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_transactions_created"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["item", "store"]),
            models.Index(fields=["cost_code"]),
            models.Index(fields=["equipment"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gt=0), name="stock_transaction_quantity_positive"),
            models.CheckConstraint(
                # Nested `class Meta` can't see StockTransaction's local `Type` name (class
                # bodies don't nest like function scopes), so this repeats the literal
                # values of Type.ISSUE / Type.ADJUSTMENT_OUT rather than referencing them —
                # keep COST_CODE_REQUIRED_TYPES above in sync if either value ever changes.
                check=~models.Q(transaction_type__in=["issue", "adjustment_out"]) | models.Q(cost_code__isnull=False),
                name="stock_transaction_issue_requires_cost_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} — {self.quantity} {self.item.unit_of_measure} {self.item.sku} @ {self.store.code}"

    @property
    def is_inbound(self) -> bool:
        return self.transaction_type in self.IN_TYPES

    @property
    def signed_quantity(self):
        return self.quantity if self.is_inbound else -self.quantity
