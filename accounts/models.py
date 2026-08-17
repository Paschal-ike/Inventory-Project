from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Role is an organization-wide capability level (what a user is generally
    allowed to do). Which specific stores/projects a Store Keeper / Quarry
    Manager / Fleet Manager can actually touch is controlled separately by
    warehouses.StoreAssignment and projects.ProjectMembership. Administrators
    bypass scoping checks entirely.
    """

    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        STORE_KEEPER = "store_keeper", "Store Keeper"
        QUARRY_MANAGER = "quarry_manager", "Quarry Manager"
        FLEET_MANAGER = "fleet_manager", "Fleet / Plant Manager"
        PROCUREMENT_OFFICER = "procurement_officer", "Procurement Officer"
        COST_ACCOUNTANT = "cost_accountant", "Project Cost Accountant / QS"
        PROJECT_MANAGER = "project_manager", "Project Manager"
        VIEWER = "viewer", "Viewer"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.VIEWER)

    @property
    def is_administrator(self) -> bool:
        return self.role == self.Role.ADMINISTRATOR

    @property
    def is_store_keeper(self) -> bool:
        return self.role == self.Role.STORE_KEEPER

    @property
    def is_quarry_manager(self) -> bool:
        return self.role == self.Role.QUARRY_MANAGER

    @property
    def is_fleet_manager(self) -> bool:
        return self.role == self.Role.FLEET_MANAGER

    @property
    def is_procurement_officer(self) -> bool:
        return self.role == self.Role.PROCUREMENT_OFFICER

    @property
    def is_cost_accountant(self) -> bool:
        return self.role == self.Role.COST_ACCOUNTANT

    @property
    def is_project_manager(self) -> bool:
        return self.role == self.Role.PROJECT_MANAGER

    def __str__(self) -> str:
        return self.get_full_name() or self.username
