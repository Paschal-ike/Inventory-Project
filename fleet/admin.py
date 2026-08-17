from django.contrib import admin

from fleet.models import Equipment, WorkOrder


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["asset_tag", "name", "equipment_class", "home_store", "fuel_type", "status", "current_meter_reading"]
    list_filter = ["equipment_class", "fuel_type", "status"]
    search_fields = ["asset_tag", "name"]
    autocomplete_fields = ["home_store"]


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "equipment", "work_type", "status", "cost_code", "opened_by", "created_at"]
    list_filter = ["work_type", "status"]
    search_fields = ["equipment__asset_tag"]
    autocomplete_fields = ["equipment", "cost_code"]
