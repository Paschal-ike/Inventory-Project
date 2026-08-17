from accounts.models import User
from accounts.permissions import can_manage_fleet, can_manage_work_orders


def can_manage_equipment(user: User) -> bool:
    return can_manage_fleet(user)


def can_open_work_order(user: User) -> bool:
    return can_manage_work_orders(user)


def can_close_work_order(user: User) -> bool:
    return can_manage_work_orders(user)
