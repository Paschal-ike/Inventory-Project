from django.contrib import admin

from procurement.models import PurchaseOrder, PurchaseOrderLine, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "contact_name", "contact_phone", "is_active"]
    list_filter = ["country", "is_active"]
    search_fields = ["name"]


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    autocomplete_fields = ["item", "cost_code"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["reference", "supplier", "store", "status", "currency", "created_at"]
    list_filter = ["status", "currency"]
    search_fields = ["reference"]
    autocomplete_fields = ["supplier", "store"]
    inlines = [PurchaseOrderLineInline]
