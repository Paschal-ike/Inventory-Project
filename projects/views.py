from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from projects import selectors, services
from projects.models import Project
from projects.permissions import can_create_project, can_edit_project, can_manage_cost_codes_for, can_view_project
from stock.selectors import store_balances_for_project


@login_required
def dashboard(request):
    projects = selectors.projects_visible_to(request.user)
    return render(request, "projects/dashboard.html", {"projects": projects})


@login_required
def project_list(request):
    return render(request, "projects/project_list.html", {"projects": selectors.projects_visible_to(request.user)})


@login_required
def project_create(request):
    if not can_create_project(request.user):
        raise PermissionDenied
    if request.method == "POST":
        project = services.create_project(
            name=request.POST.get("name", ""),
            code=request.POST.get("code", ""),
            description=request.POST.get("description", ""),
            currency=request.POST.get("currency", Project.Currency.NGN),
            created_by=request.user,
        )
        messages.success(request, f"Project “{project.name}” created.")
        return redirect("projects:project_detail", pk=project.pk)
    return render(request, "projects/project_form.html", {"currencies": Project.Currency.choices})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not can_view_project(request.user, project):
        raise PermissionDenied
    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "cost_codes": selectors.active_cost_codes_for(project),
            "members": project.memberships.select_related("user"),
            "balances": store_balances_for_project(project),
            "can_edit": can_edit_project(request.user, project),
            "can_manage_cost_codes": can_manage_cost_codes_for(request.user, project),
        },
    )


@login_required
def project_add_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        user = get_object_or_404(User, pk=request.POST.get("user_id"))
        services.add_member(project=project, user=user, actor=request.user)
        messages.success(request, f"Added {user} to {project.name}.")
    return redirect("projects:project_detail", pk=project.pk)


@login_required
def project_remove_member(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    user = get_object_or_404(User, pk=user_id)
    services.remove_member(project=project, user=user, actor=request.user)
    messages.success(request, f"Removed {user} from {project.name}.")
    return redirect("projects:project_detail", pk=project.pk)


@login_required
def cost_code_create(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        code = request.POST.get("code", "")
        try:
            services.create_cost_code(
                project=project,
                code=code,
                description=request.POST.get("description", ""),
                budget_amount=request.POST.get("budget_amount") or None,
                created_by=request.user,
            )
            messages.success(request, "Cost code created.")
        except IntegrityError:
            messages.error(request, f"Cost code “{code}” already exists on this project.")
    return redirect("projects:project_detail", pk=project.pk)
