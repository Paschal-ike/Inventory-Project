"""
Combines an org-wide capability (accounts.permissions) with store scope
(warehouses.permissions.can_transact_in_store) for each transaction type the
ledger supports.
"""
from accounts.models import User
from accounts.permissions import can_adjust_stock, can_issue_stock, can_log_quarry_production, can_receive_purchase
from accounts.permissions import can_transfer_stock as _can_transfer_stock_role
from warehouses.models import Store
from warehouses.permissions import can_transact_in_store


def can_log_quarry_receipt(user: User, stockyard: Store) -> bool:
    return can_log_quarry_production(user) and can_transact_in_store(user, stockyard)


def can_receive_stock(user: User, store: Store) -> bool:
    if not can_receive_purchase(user):
        return False
    # Procurement is centralized, not site-based — a procurement officer buys
    # for whichever site a PO is destined for, so (unlike a store keeper) they
    # aren't restricted to stores they hold a StoreAssignment at.
    if user.is_authenticated and user.is_procurement_officer:
        return True
    return can_transact_in_store(user, store)


def can_transfer_stock(user: User, source_store: Store) -> bool:
    return _can_transfer_stock_role(user) and can_transact_in_store(user, source_store)


def can_issue_from(user: User, store: Store) -> bool:
    return can_issue_stock(user) and can_transact_in_store(user, store)


def can_adjust(user: User, store: Store) -> bool:
    return can_adjust_stock(user) and can_transact_in_store(user, store)
