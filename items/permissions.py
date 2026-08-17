from accounts.models import User
from accounts.permissions import can_manage_master_data


def can_manage_items(user: User) -> bool:
    return can_manage_master_data(user)
