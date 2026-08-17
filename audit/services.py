from django.contrib.contenttypes.models import ContentType
from django.db import models

from audit.models import AuditLogEntry


def log_event(*, actor, action: str, description: str, target: models.Model | None = None, project=None) -> AuditLogEntry:
    return AuditLogEntry.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        description=description,
        project=project,
        content_type=ContentType.objects.get_for_model(target) if target is not None else None,
        object_id=target.pk if target is not None else None,
    )
