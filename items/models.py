from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Item(TimeStampedModel):
    class Category(models.TextChoices):
        AGGREGATE = "aggregate", "Aggregate (quarried material)"
        FUEL = "fuel", "Diesel / Fuel"
        SPARE_PART = "spare_part", "Spare Part"
        CONSUMABLE = "consumable", "Consumable"
        TOOL = "tool", "Tool"

    class ValuationMethod(models.TextChoices):
        WEIGHTED_AVERAGE = "weighted_average", "Weighted Average"
        STANDARD_COST = "standard_cost", "Standard Cost"

    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=16, choices=Category.choices)
    unit_of_measure = models.CharField(max_length=16, help_text="e.g. tonne, litre, piece")
    valuation_method = models.CharField(
        max_length=20, choices=ValuationMethod.choices, default=ValuationMethod.WEIGHTED_AVERAGE
    )
    reorder_level = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="items_created"
    )

    class Meta:
        ordering = ["sku"]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"

    @property
    def is_aggregate(self) -> bool:
        return self.category == self.Category.AGGREGATE

    @property
    def is_fuel(self) -> bool:
        return self.category == self.Category.FUEL
