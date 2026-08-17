"""
Organization-wide capability checks based on accounts.User.role.
Store/project-scoped access is handled in warehouses.permissions and
projects.permissions.
"""
from accounts.models import User


def can_manage_users(user: User) -> bool:
    return user.is_authenticated and user.is_administrator


def can_manage_master_data(user: User) -> bool:
    """Create/edit stores, items, equipment — structural data, not transactions."""
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.PROCUREMENT_OFFICER}


def can_log_quarry_production(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.QUARRY_MANAGER}


def can_transfer_stock(user: User) -> bool:
    return user.is_authenticated and user.role in {
        User.Role.ADMINISTRATOR,
        User.Role.STORE_KEEPER,
        User.Role.QUARRY_MANAGER,
    }


def can_issue_stock(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.STORE_KEEPER}


def can_receive_purchase(user: User) -> bool:
    return user.is_authenticated and user.role in {
        User.Role.ADMINISTRATOR,
        User.Role.STORE_KEEPER,
        User.Role.PROCUREMENT_OFFICER,
    }


def can_adjust_stock(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.STORE_KEEPER}


def can_manage_fleet(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.FLEET_MANAGER}


def can_manage_work_orders(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.FLEET_MANAGER}


def can_manage_procurement(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.PROCUREMENT_OFFICER}


def can_manage_cost_codes(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.COST_ACCOUNTANT}


def can_view_cost_reports(user: User) -> bool:
    return user.is_authenticated and user.role in {
        User.Role.ADMINISTRATOR,
        User.Role.COST_ACCOUNTANT,
        User.Role.PROJECT_MANAGER,
    }
