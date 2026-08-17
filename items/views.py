from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from items import selectors, services
from items.models import Item
from items.permissions import can_manage_items


@login_required
def item_list(request):
    return render(request, "items/item_list.html", {"items": selectors.active_items()})


@login_required
def item_create(request):
    if not can_manage_items(request.user):
        raise PermissionDenied
    if request.method == "POST":
        services.create_item(
            sku=request.POST.get("sku", ""),
            name=request.POST.get("name", ""),
            category=request.POST.get("category", ""),
            unit_of_measure=request.POST.get("unit_of_measure", ""),
            valuation_method=request.POST.get("valuation_method", Item.ValuationMethod.WEIGHTED_AVERAGE),
            reorder_level=request.POST.get("reorder_level") or 0,
            created_by=request.user,
        )
        messages.success(request, "Item created.")
        return redirect("items:item_list")
    return render(
        request,
        "items/item_form.html",
        {"categories": Item.Category.choices, "valuation_methods": Item.ValuationMethod.choices},
    )
