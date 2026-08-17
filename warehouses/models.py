from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Country(models.TextChoices):
    NIGERIA = "NG", "Nigeria"
    TOGO = "TG", "Togo"
    BENIN = "BJ", "Benin"


class Store(TimeStampedModel):
    """
    A physical stock point. The hierarchy this project needs is
    state/country -> project/site -> store, modelled here as a self-FK
    (parent) rather than a fixed depth, since a central depot feeding
    several state depots feeding several site stores is a real shape and a
    fixed-depth model would fight it.
    """

    class StoreType(models.TextChoices):
        CENTRAL_DEPOT = "central_depot", "Central Depot"
        STATE_DEPOT = "state_depot", "State / Regional Depot"
        PROJECT_SITE_STORE = "project_site_store", "Project Site Store"
        QUARRY_STOCKYARD = "quarry_stockyard", "Quarry Stockyard"

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, unique=True, help_text="e.g. LAG-EPE-01")
    store_type = models.CharField(max_length=32, choices=StoreType.choices)
    country = models.CharField(max_length=2, choices=Country.choices, default=Country.NIGERIA)
    state_or_region = models.CharField(
        max_length=64, help_text="Nigerian state, or region within Togo/Benin"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stores",
        help_text="Set for a project site store; blank for a central/state depot or quarry stockyard.",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="child_stores"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stores_created"
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class StoreAssignment(TimeStampedModel):
    """Scopes which stores a Store Keeper / Quarry Manager can transact against."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="store_assignments"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["store", "user"], name="unique_store_assignment"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.store}"


class Quarry(TimeStampedModel):
    """
    A production site — Calabar, Ore, Abuja, Sokode. The source side of an
    internal transfer, never a purchase order. `stockyard` is the Store that
    holds whatever the quarry has produced but not yet transferred out.
    """

    name = models.CharField(max_length=255)
    stockyard = models.OneToOneField(Store, on_delete=models.PROTECT, related_name="quarry")
    country = models.CharField(max_length=2, choices=Country.choices, default=Country.NIGERIA)
    location = models.CharField(max_length=255, blank=True)
    licensed_material_types = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated, e.g. 'granite, laterite, sand'"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quarries_created"
    )

    class Meta:
        verbose_name_plural = "quarries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
