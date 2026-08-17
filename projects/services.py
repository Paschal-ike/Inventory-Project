from django.core.exceptions import PermissionDenied
from django.db import transaction

from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event
from projects.models import CostCode, Project, ProjectMembership
from projects.permissions import can_create_project, can_edit_project, can_manage_cost_codes_for, can_manage_membership


@transaction.atomic
def create_project(*, name: str, code: str, description: str, currency: str, created_by: User) -> Project:
    if not can_create_project(created_by):
        raise PermissionDenied("You do not have permission to create projects.")
    project = Project.objects.create(
        name=name, code=code, description=description, currency=currency, created_by=created_by
    )
    ProjectMembership.objects.create(project=project, user=created_by, added_by=created_by)
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.PROJECT_CREATED,
        description=f"Created project {project.code!r} — {project.name}",
        target=project,
        project=project,
    )
    return project


def update_project(*, project: Project, name: str, description: str, status: str, actor: User) -> Project:
    if not can_edit_project(actor, project):
        raise PermissionDenied("You do not have permission to edit this project.")
    project.name = name
    project.description = description
    project.status = status
    project.save(update_fields=["name", "description", "status", "updated_at"])
    return project


def add_member(*, project: Project, user: User, actor: User) -> ProjectMembership:
    if not can_manage_membership(actor, project):
        raise PermissionDenied("You do not have permission to manage members on this project.")
    membership, _ = ProjectMembership.objects.get_or_create(
        project=project, user=user, defaults={"added_by": actor}
    )
    return membership


def remove_member(*, project: Project, user: User, actor: User) -> None:
    if not can_manage_membership(actor, project):
        raise PermissionDenied("You do not have permission to manage members on this project.")
    ProjectMembership.objects.filter(project=project, user=user).delete()


@transaction.atomic
def create_cost_code(
    *,
    project: Project | None,
    code: str,
    description: str,
    budget_amount,
    created_by: User,
) -> CostCode:
    if not can_manage_cost_codes_for(created_by, project):
        raise PermissionDenied("You do not have permission to create cost codes here.")
    cost_code = CostCode.objects.create(
        project=project,
        code=code,
        description=description,
        budget_amount=budget_amount,
        created_by=created_by,
    )
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.COST_CODE_CREATED,
        description=f"Created cost code {cost_code.code!r}"
        + (f" on project {project.code}" if project else " (plant overhead)"),
        target=cost_code,
        project=project,
    )
    return cost_code


def deactivate_cost_code(*, cost_code: CostCode, actor: User) -> CostCode:
    if not can_manage_cost_codes_for(actor, cost_code.project):
        raise PermissionDenied("You do not have permission to deactivate this cost code.")
    cost_code.is_active = False
    cost_code.save(update_fields=["is_active", "updated_at"])
    return cost_code
