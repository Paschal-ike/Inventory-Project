from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from fleet.models import Equipment, WorkOrder
from items.models import Item
from projects.models import CostCode
from stock import selectors, services
from stock.permissions import can_adjust, can_issue_from, can_log_quarry_receipt, can_receive_stock, can_transfer_stock
from warehouses.models import Quarry, Store
from warehouses.permissions import can_view_store


@login_required
def store_ledger(request, store_pk):
    store = get_object_or_404(Store, pk=store_pk)
    if not can_view_store(request.user, store):
        raise PermissionDenied
    return render(
        request,
        "stock/store_ledger.html",
        {
            "store": store,
            "balances": selectors.balance_for_store(store),
            "transactions": selectors.recent_transactions_for_store(store),
            "quarry": getattr(store, "quarry", None),
        },
    )


@login_required
def quarry_receipt_form(request, quarry_pk):
    quarry = get_object_or_404(Quarry, pk=quarry_pk)
    if not can_log_quarry_receipt(request.user, quarry.stockyard):
        raise PermissionDenied
    if request.method == "POST":
        try:
            services.log_quarry_production(
                quarry=quarry,
                item=get_object_or_404(Item, pk=request.POST["item"]),
                quantity=request.POST["quantity"],
                unit_cost=request.POST["unit_cost"],
                reference=request.POST.get("reference", ""),
                actor=request.user,
            )
            messages.success(request, "Production logged.")
            return redirect("stock:store_ledger", store_pk=quarry.stockyard_id)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "stock/quarry_receipt_form.html",
        {"quarry": quarry, "items": Item.objects.filter(is_active=True, category=Item.Category.AGGREGATE)},
    )


@login_required
def issue_form(request, store_pk):
    store = get_object_or_404(Store, pk=store_pk)
    if not can_issue_from(request.user, store):
        raise PermissionDenied
    if request.method == "POST":
        try:
            equipment = None
            if request.POST.get("equipment"):
                equipment = get_object_or_404(Equipment, pk=request.POST["equipment"])
            work_order = None
            if request.POST.get("work_order"):
                work_order = get_object_or_404(WorkOrder, pk=request.POST["work_order"])
            cost_code = None
            if request.POST.get("cost_code"):
                cost_code = get_object_or_404(CostCode, pk=request.POST["cost_code"])
            services.issue_stock(
                store=store,
                item=get_object_or_404(Item, pk=request.POST["item"]),
                quantity=request.POST["quantity"],
                cost_code=cost_code,
                equipment=equipment,
                work_order=work_order,
                meter_reading=request.POST.get("meter_reading") or None,
                reference=request.POST.get("reference", ""),
                actor=request.user,
            )
            messages.success(request, "Stock issued.")
            return redirect("stock:store_ledger", store_pk=store.pk)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "stock/issue_form.html",
        {
            "store": store,
            "items": Item.objects.filter(is_active=True),
            "equipment": Equipment.objects.filter(status=Equipment.Status.ACTIVE),
            "cost_codes": CostCode.objects.filter(is_active=True),
        },
    )


@login_required
def transfer_form(request, store_pk):
    source_store = get_object_or_404(Store, pk=store_pk)
    if not can_transfer_stock(request.user, source_store):
        raise PermissionDenied
    if request.method == "POST":
        try:
            services.transfer_stock(
                source_store=source_store,
                destination_store=get_object_or_404(Store, pk=request.POST["destination_store"]),
                item=get_object_or_404(Item, pk=request.POST["item"]),
                quantity=request.POST["quantity"],
                reference=request.POST.get("reference", ""),
                actor=request.user,
            )
            messages.success(request, "Stock transferred.")
            return redirect("stock:store_ledger", store_pk=source_store.pk)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "stock/transfer_form.html",
        {
            "store": source_store,
            "items": Item.objects.filter(is_active=True),
            "destination_stores": Store.objects.filter(is_active=True).exclude(pk=source_store.pk),
        },
    )


@login_required
def receive_form(request, store_pk):
    store = get_object_or_404(Store, pk=store_pk)
    if not can_receive_stock(request.user, store):
        raise PermissionDenied
    if request.method == "POST":
        try:
            services.receive_purchase(
                store=store,
                item=get_object_or_404(Item, pk=request.POST["item"]),
                quantity=request.POST["quantity"],
                unit_cost=request.POST["unit_cost"],
                reference=request.POST.get("reference", ""),
                actor=request.user,
            )
            messages.success(request, "Purchase receipt recorded.")
            return redirect("stock:store_ledger", store_pk=store.pk)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return render(request, "stock/receive_form.html", {"store": store, "items": Item.objects.filter(is_active=True)})


@login_required
def adjust_form(request, store_pk):
    store = get_object_or_404(Store, pk=store_pk)
    if not can_adjust(request.user, store):
        raise PermissionDenied
    if request.method == "POST":
        try:
            cost_code = None
            if request.POST.get("cost_code"):
                cost_code = get_object_or_404(CostCode, pk=request.POST["cost_code"])
            txn = services.adjust_stock(
                store=store,
                item=get_object_or_404(Item, pk=request.POST["item"]),
                counted_quantity=request.POST["counted_quantity"],
                cost_code=cost_code,
                reference=request.POST.get("reference", ""),
                actor=request.user,
            )
            messages.success(request, "No variance found." if txn is None else "Stock count variance recorded.")
            return redirect("stock:store_ledger", store_pk=store.pk)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "stock/adjust_form.html",
        {
            "store": store,
            "items": Item.objects.filter(is_active=True),
            "cost_codes": CostCode.objects.filter(is_active=True),
        },
    )
