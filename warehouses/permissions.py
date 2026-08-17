"""
Object-level access predicates for Store. Combines an org-wide capability
(accounts.permissions) with store scope (StoreAssignment) — mirrors the
project/membership split in projects.permissions.
"""
from accounts.models import User
from accounts.permissions import can_manage_master_data
from warehouses.models import Store


def is_assigned(user: User, store: Store) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_administrator:
        return True
    return store.assignments.filter(user=user).exists()


def can_view_store(user: User, store: Store) -> bool:
    return is_assigned(user, store)


def can_transact_in_store(user: User, store: Store) -> bool:
    """Receive/issue/transfer/count stock at this store — role capability plus assignment."""
    if not user.is_authenticated:
        return False
    if user.is_administrator:
        return True
    return is_assigned(user, store)


def can_manage_store(user: User) -> bool:
    return can_manage_master_data(user)


def can_manage_store_assignments(user: User, store: Store) -> bool:
    return user.is_authenticated and (user.is_administrator or can_manage_master_data(user))
