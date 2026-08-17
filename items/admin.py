from django.contrib import admin

from items.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "category", "unit_of_measure", "valuation_method", "reorder_level", "is_active"]
    list_filter = ["category", "valuation_method", "is_active"]
    search_fields = ["sku", "name"]
