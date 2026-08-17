from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from fleet import selectors, services
from fleet.models import Equipment, WorkOrder
from fleet.permissions import can_manage_equipment, can_open_work_order
from projects.models import CostCode
from stock.selectors import transactions_for_equipment
from warehouses.models import Store


@login_required
def equipment_list(request):
    return render(request, "fleet/equipment_list.html", {"equipment": selectors.active_equipment()})


@login_required
def equipment_create(request):
    if not can_manage_equipment(request.user):
        raise PermissionDenied
    if request.method == "POST":
        equipment = services.create_equipment(
            asset_tag=request.POST.get("asset_tag", ""),
            name=request.POST.get("name", ""),
            equipment_class=request.POST.get("equipment_class", ""),
            home_store=get_object_or_404(Store, pk=request.POST.get("home_store")),
            meter_type=request.POST.get("meter_type", Equipment.MeterType.HOURS),
            fuel_type=request.POST.get("fuel_type", Equipment.FuelType.DIESEL),
            created_by=request.user,
        )
        messages.success(request, f"Equipment “{equipment.asset_tag}” registered.")
        return redirect("fleet:equipment_detail", pk=equipment.pk)
    return render(
        request,
        "fleet/equipment_form.html",
        {
            "stores": Store.objects.filter(is_active=True),
            "meter_types": Equipment.MeterType.choices,
            "fuel_types": Equipment.FuelType.choices,
        },
    )


@login_required
def equipment_detail(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    return render(
        request,
        "fleet/equipment_detail.html",
        {
            "equipment": equipment,
            "work_orders": equipment.work_orders.all()[:50],
            "transactions": transactions_for_equipment(equipment)[:50],
            "cost_codes": CostCode.objects.filter(is_active=True),
        },
    )


@login_required
def work_order_create(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if not can_open_work_order(request.user):
        raise PermissionDenied
    if request.method == "POST":
        cost_code_id = request.POST.get("cost_code")
        cost_code = get_object_or_404(CostCode, pk=cost_code_id) if cost_code_id else None
        services.open_work_order(
            equipment=equipment,
            work_type=request.POST.get("work_type", WorkOrder.WorkType.BREAKDOWN),
            description=request.POST.get("description", ""),
            cost_code=cost_code,
            opened_by=request.user,
        )
        messages.success(request, "Work order opened.")
    return redirect("fleet:equipment_detail", pk=equipment.pk)


@login_required
def work_order_close(request, pk):
    work_order = get_object_or_404(WorkOrder, pk=pk)
    services.close_work_order(work_order=work_order, actor=request.user)
    messages.success(request, f"{work_order} closed.")
    return redirect("fleet:equipment_detail", pk=work_order.equipment_id)
