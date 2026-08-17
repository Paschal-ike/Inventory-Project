from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    class Currency(models.TextChoices):
        NGN = "NGN", "Nigerian Naira"
        XOF = "XOF", "West African CFA Franc"

    name = models.CharField(max_length=255)
    code = models.CharField(
        "Project code", max_length=32, unique=True, help_text="Short code used as the cost-code prefix, e.g. EPE-EXP."
    )
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.NGN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="projects_created"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ProjectMembership(TimeStampedModel):
    """
    Scopes which projects a Project Manager / Cost Accountant / Store Keeper
    can access. Capability (what they're allowed to do) comes from the
    user's org-wide role (accounts.User.role); this model only answers "can
    this user see this project at all". Administrators bypass this check.
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="unique_project_membership"),
        ]

    def __str__(self) -> str:
        return f"{self.user} on {self.project}"


class CostCode(TimeStampedModel):
    """
    The thing every stock issue must ultimately land on. Either a project's
    BOQ/contract line (project is set) or a general plant-overhead code for
    non-billable running cost — routine maintenance, general fleet fuel not
    chargeable to a single job (project is null).
    """

    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, null=True, blank=True, related_name="cost_codes"
    )
    code = models.CharField(max_length=32, help_text="e.g. 025-EARTHWORKS or PLANT-OVERHEAD-FUEL")
    description = models.CharField(max_length=255)
    budget_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cost_codes_created"
    )

    class Meta:
        constraints = [
            # Plain UniqueConstraint(["project", "code"]) would not catch
            # duplicates between two overhead codes (project IS NULL on both
            # sides) — Postgres treats NULLs as distinct for uniqueness — so
            # the null case gets its own conditional constraint on code alone.
            models.UniqueConstraint(
                fields=["project", "code"],
                condition=models.Q(project__isnull=False),
                name="unique_cost_code_per_project",
            ),
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(project__isnull=True),
                name="unique_overhead_cost_code",
            ),
        ]
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} ({self.project.code if self.project else 'overhead'})"

    @property
    def is_overhead(self) -> bool:
        return self.project_id is None
