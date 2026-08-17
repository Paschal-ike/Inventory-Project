from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Equipment(TimeStampedModel):
    """A plant/vehicle unit — the thing fuel and spares get issued against."""

    class MeterType(models.TextChoices):
        HOURS = "hours", "Hour meter"
        ODOMETER = "odometer", "Odometer"

    class FuelType(models.TextChoices):
        DIESEL = "diesel", "Diesel (AGO)"
        PETROL = "petrol", "Petrol (PMS)"
        ELECTRIC = "electric", "Electric"
        NONE = "none", "None (non-powered)"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNDER_MAINTENANCE = "under_maintenance", "Under Maintenance"
        DECOMMISSIONED = "decommissioned", "Decommissioned"

    asset_tag = models.CharField(max_length=32, unique=True, help_text="e.g. EXC-0142")
    name = models.CharField(max_length=255)
    equipment_class = models.CharField(
        max_length=64, help_text="e.g. Excavator, Dump Truck, Grader, Asphalt Paver"
    )
    home_store = models.ForeignKey(
        "warehouses.Store", on_delete=models.PROTECT, related_name="home_equipment"
    )
    meter_type = models.CharField(max_length=16, choices=MeterType.choices, default=MeterType.HOURS)
    fuel_type = models.CharField(max_length=16, choices=FuelType.choices, default=FuelType.DIESEL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_meter_reading = models.DecimalField(max_digits=12, decimal_places=1, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="equipment_created"
    )

    class Meta:
        verbose_name_plural = "equipment"
        ordering = ["asset_tag"]

    def __str__(self) -> str:
        return f"{self.asset_tag} — {self.name}"


class WorkOrder(TimeStampedModel):
    """
    A maintenance job against one equipment unit — the link between a spare
    part or fuel issue and the reason it happened. Whether it carries a cost
    code decides whether the parts issued against it bill a project or land
    on general plant overhead.
    """

    class WorkType(models.TextChoices):
        BREAKDOWN = "breakdown", "Breakdown"
        PREVENTIVE_MAINTENANCE = "preventive_maintenance", "Preventive Maintenance"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"

    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="work_orders")
    work_type = models.CharField(max_length=24, choices=WorkType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    description = models.TextField(blank=True)
    cost_code = models.ForeignKey(
        "projects.CostCode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="work_orders",
        help_text="Set if this job is billable to a project; leave blank for routine plant-overhead maintenance.",
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="work_orders_opened"
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"WO-{self.pk} — {self.equipment.asset_tag} ({self.get_status_display()})"
