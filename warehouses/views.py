from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from stock.selectors import balance_for_store
from warehouses import selectors, services
from warehouses.models import Store
from warehouses.permissions import can_manage_store, can_view_store


@login_required
def store_list(request):
    return render(request, "warehouses/store_list.html", {"stores": selectors.stores_visible_to(request.user)})


@login_required
def store_create(request):
    if not can_manage_store(request.user):
        raise PermissionDenied
    if request.method == "POST":
        store = services.create_store(
            name=request.POST.get("name", ""),
            code=request.POST.get("code", ""),
            store_type=request.POST.get("store_type", ""),
            country=request.POST.get("country", ""),
            state_or_region=request.POST.get("state_or_region", ""),
            created_by=request.user,
        )
        messages.success(request, f"Store “{store.name}” created.")
        return redirect("warehouses:store_detail", pk=store.pk)
    return render(
        request,
        "warehouses/store_form.html",
        {"store_types": Store.StoreType.choices},
    )


@login_required
def store_detail(request, pk):
    store = get_object_or_404(Store, pk=pk)
    if not can_view_store(request.user, store):
        raise PermissionDenied
    return render(
        request,
        "warehouses/store_detail.html",
        {
            "store": store,
            "balances": balance_for_store(store),
            "assignments": store.assignments.select_related("user"),
        },
    )
