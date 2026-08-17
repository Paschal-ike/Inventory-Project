from django.contrib import admin

from stock.models import StockTransaction


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "transaction_type",
        "item",
        "store",
        "quantity",
        "unit_cost",
        "cost_code",
        "equipment",
        "created_by",
    ]
    list_filter = ["transaction_type", "store", "item__category"]
    search_fields = ["item__sku", "reference", "equipment__asset_tag"]
    autocomplete_fields = ["item", "store", "cost_code", "equipment", "work_order", "related_transaction"]
    readonly_fields = ["related_transaction"]

    def has_change_permission(self, request, obj=None):
        # Append-only ledger — corrections are reversing entries, not edits.
        return False
