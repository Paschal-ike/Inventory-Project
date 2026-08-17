from django.contrib import admin

from warehouses.models import Quarry, Store, StoreAssignment


class StoreAssignmentInline(admin.TabularInline):
    model = StoreAssignment
    extra = 1
    fk_name = "store"
    autocomplete_fields = ["user"]
    readonly_fields = ["added_by"]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "store_type", "country", "state_or_region", "project", "is_active"]
    list_filter = ["store_type", "country", "is_active"]
    search_fields = ["code", "name", "state_or_region"]
    autocomplete_fields = ["project", "parent"]
    inlines = [StoreAssignmentInline]


@admin.register(Quarry)
class QuarryAdmin(admin.ModelAdmin):
    list_display = ["name", "stockyard", "country", "location"]
    list_filter = ["country"]
    search_fields = ["name", "location"]
    autocomplete_fields = ["stockyard"]
