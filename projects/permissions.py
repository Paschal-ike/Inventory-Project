"""
Object-level access predicates for Project/CostCode. Combine an org-wide
capability (accounts.permissions) with project scope (ProjectMembership) —
used by both template views and, later, DRF permission classes so the logic
lives once.
"""
from accounts.models import User
from accounts.permissions import can_manage_cost_codes
from projects.models import CostCode, Project


def can_create_project(user: User) -> bool:
    return user.is_authenticated and user.role in {User.Role.ADMINISTRATOR, User.Role.PROJECT_MANAGER}


def is_member(user: User, project: Project) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_administrator:
        return True
    return project.memberships.filter(user=user).exists()


def can_view_project(user: User, project: Project) -> bool:
    return is_member(user, project)


def can_edit_project(user: User, project: Project) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_administrator:
        return True
    return user.is_project_manager and is_member(user, project)


def can_manage_membership(user: User, project: Project) -> bool:
    return can_edit_project(user, project)


def can_manage_cost_codes_for(user: User, project: Project | None) -> bool:
    """project is None for a general plant-overhead code — those are admin/cost-accountant only,
    with no membership scope to check since they don't belong to any single project."""
    if not can_manage_cost_codes(user):
        return False
    if project is None:
        return True
    return is_member(user, project)


def can_use_cost_code(user: User, cost_code: CostCode) -> bool:
    """Broader than can_manage: anyone issuing stock needs to be able to pick a valid
    cost code for their project, not just the accountant who created it."""
    if not user.is_authenticated:
        return False
    if user.is_administrator:
        return True
    if cost_code.project_id is None:
        return True
    return is_member(user, cost_code.project)
