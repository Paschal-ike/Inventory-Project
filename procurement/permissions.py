from accounts.models import User
from accounts.permissions import can_manage_procurement


def can_manage_suppliers(user: User) -> bool:
    return can_manage_procurement(user)


def can_create_purchase_order(user: User) -> bool:
    return can_manage_procurement(user)
