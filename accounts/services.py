from accounts.forms import UserCreateForm
from accounts.models import User
from audit.models import AuditLogEntry
from audit.services import log_event


def create_user(*, form: UserCreateForm, created_by: User) -> User:
    user = form.save()
    log_event(
        actor=created_by,
        action=AuditLogEntry.Action.USER_CREATED,
        description=f"Created user {user.username!r} with role {user.get_role_display()}",
        target=user,
    )
    return user
