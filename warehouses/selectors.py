from django.db.models import QuerySet

from accounts.models import User
from warehouses.models import Quarry, Store


def stores_visible_to(user: User) -> QuerySet[Store]:
    if not user.is_authenticated:
        return Store.objects.none()
    if user.is_administrator:
        return Store.objects.filter(is_active=True)
    return Store.objects.filter(is_active=True, assignments__user=user).distinct()


def stores_for_project(project) -> QuerySet[Store]:
    return Store.objects.filter(project=project, is_active=True)


def all_quarries() -> QuerySet[Quarry]:
    return Quarry.objects.select_related("stockyard").order_by("name")


def assignable_users_for(store: Store) -> QuerySet[User]:
    existing_ids = store.assignments.values_list("user_id", flat=True)
    return User.objects.exclude(id__in=existing_ids).order_by("username")
