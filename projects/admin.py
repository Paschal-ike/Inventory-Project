from django.contrib import admin

from projects.models import CostCode, Project, ProjectMembership


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    fk_name = "project"
    autocomplete_fields = ["user"]
    readonly_fields = ["added_by"]


class CostCodeInline(admin.TabularInline):
    model = CostCode
    extra = 0
    fields = ["code", "description", "budget_amount", "is_active"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "status", "currency", "created_by", "created_at"]
    list_filter = ["status", "currency"]
    search_fields = ["code", "name"]
    inlines = [ProjectMembershipInline, CostCodeInline]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ["project", "user", "added_by", "created_at"]
    autocomplete_fields = ["project", "user"]


@admin.register(CostCode)
class CostCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "project", "description", "budget_amount", "is_active"]
    list_filter = ["is_active", "project"]
    search_fields = ["code", "description"]
    autocomplete_fields = ["project"]
