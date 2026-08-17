from django.conf import settings
from django.db import models

from common.models import TimeStampedModel
from warehouses.models import Country


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    contact_email = models.EmailField(blank=True)
    country = models.CharField(max_length=2, choices=Country.choices, default=Country.NIGERIA)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="suppliers_created"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ORDERED = "ordered", "Ordered"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    class Currency(models.TextChoices):
        NGN = "NGN", "Nigerian Naira"
        XOF = "XOF", "West African CFA Franc"

    reference = models.CharField(max_length=32, unique=True, help_text="e.g. PO-2026-0142")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    store = models.ForeignKey(
        "warehouses.Store", on_delete=models.PROTECT, related_name="purchase_orders", help_text="Delivery / GRN store."
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.NGN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="purchase_orders_created"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.reference


class PurchaseOrderLine(TimeStampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("items.Item", on_delete=models.PROTECT, related_name="purchase_order_lines")
    quantity_ordered = models.DecimalField(max_digits=14, decimal_places=3)
    quantity_received = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    cost_code = models.ForeignKey(
        "projects.CostCode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_order_lines",
        help_text="Intended allocation at receipt — the GRN still posts through stock.services.receive_purchase.",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.purchase_order.reference}: {self.quantity_ordered} {self.item.sku}"

    @property
    def quantity_outstanding(self):
        return self.quantity_ordered - self.quantity_received
