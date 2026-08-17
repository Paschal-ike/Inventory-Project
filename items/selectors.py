from django.db.models import QuerySet

from items.models import Item


def active_items() -> QuerySet[Item]:
    return Item.objects.filter(is_active=True)


def items_by_category(category: str) -> QuerySet[Item]:
    return active_items().filter(category=category)
