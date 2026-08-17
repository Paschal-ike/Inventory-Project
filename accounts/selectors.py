from django.db.models import QuerySet

from accounts.models import User


def all_users() -> QuerySet[User]:
    return User.objects.all().order_by("username")
