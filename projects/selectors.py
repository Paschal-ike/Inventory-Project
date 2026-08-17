from django.db.models import QuerySet

from accounts.models import User
from projects.models import CostCode, Project


def projects_visible_to(user: User) -> QuerySet[Project]:
    if not user.is_authenticated:
        return Project.objects.none()
    if user.is_administrator:
        return Project.objects.all()
    return Project.objects.filter(memberships__user=user).distinct()


def active_cost_codes_for(project: Project) -> QuerySet[CostCode]:
    return project.cost_codes.filter(is_active=True).order_by("code")


def overhead_cost_codes() -> QuerySet[CostCode]:
    return CostCode.objects.filter(project__isnull=True, is_active=True).order_by("code")


def cost_codes_selectable_by(user: User, project: Project | None) -> QuerySet[CostCode]:
    """Every cost code a user could pick when issuing stock against `project`
    (or against no project, for a plant-overhead issue)."""
    if project is not None:
        return active_cost_codes_for(project)
    return overhead_cost_codes()


def addable_members_for_project(project: Project) -> QuerySet[User]:
    existing_ids = project.memberships.values_list("user_id", flat=True)
    return User.objects.exclude(id__in=existing_ids).order_by("username")
