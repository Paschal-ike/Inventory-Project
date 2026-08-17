from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from procurement import selectors, services
from procurement.models import PurchaseOrder, PurchaseOrderLine


@login_required
def purchase_order_list(request):
    return render(request, "procurement/purchase_order_list.html", {"purchase_orders": selectors.open_purchase_orders()})


@login_required
def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, "procurement/purchase_order_detail.html", {"po": po, "lines": po.lines.select_related("item")})


@login_required
def receive_line(request, pk):
    line = get_object_or_404(PurchaseOrderLine, pk=pk)
    if request.method == "POST":
        try:
            services.receive_purchase_order_line(line=line, quantity=request.POST["quantity"], actor=request.user)
            messages.success(request, "Goods receipt recorded.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
    return redirect("procurement:purchase_order_detail", pk=line.purchase_order_id)
