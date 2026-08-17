from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from common.models import TimeStampedModel


class AuditLogEntry(TimeStampedModel):
    class Action(models.TextChoices):
        USER_CREATED = "user_created", "User Created"
        PASSWORD_CHANGED = "password_changed", "Password Changed"
        PROJECT_CREATED = "project_created", "Project Created"
        COST_CODE_CREATED = "cost_code_created", "Cost Code Created"
        STORE_CREATED = "store_created", "Store Created"
        ITEM_CREATED = "item_created", "Item Created"
        EQUIPMENT_CREATED = "equipment_created", "Equipment Created"
        WORK_ORDER_OPENED = "work_order_opened", "Work Order Opened"
        WORK_ORDER_CLOSED = "work_order_closed", "Work Order Closed"
        QUARRY_PRODUCTION_LOGGED = "quarry_production_logged", "Quarry Production Logged"
        PURCHASE_RECEIPT = "purchase_receipt", "Purchase Receipt"
        INTERNAL_TRANSFER = "internal_transfer", "Internal Transfer"
        STOCK_ISSUE = "stock_issue", "Stock Issue"
        STOCK_RETURN = "stock_return", "Stock Return"
        STOCK_ADJUSTMENT = "stock_adjustment", "Stock Adjustment"
        STOCK_COUNT_RECORDED = "stock_count_recorded", "Stock Count Recorded"
        PURCHASE_REQUISITION_CREATED = "purchase_requisition_created", "Purchase Requisition Created"
        PURCHASE_ORDER_CREATED = "purchase_order_created", "Purchase Order Created"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_entries"
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    description = models.TextField()
    project = models.ForeignKey(
        "projects.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_entries"
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "audit log entries"

    def __str__(self) -> str:
        return f"{self.get_action_display()} — {self.description}"
