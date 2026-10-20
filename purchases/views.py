from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import PurchaseOrder, PurchaseOrderItem, Supplier
from inventory.models import SparePart
import uuid

@login_required
def purchase_order_list_view(request):
    orders = PurchaseOrder.objects.select_related('supplier').prefetch_related('items__part').all().order_by('-created_at')
    return render(request, 'purchases/list.html', {'orders': orders})

@login_required
def purchase_order_create_view(request):
    if request.method == "POST":
        supplier_id = request.POST.get('supplier_id')
        part_id = request.POST.get('part_id')
        quantity = int(request.POST.get('quantity'))
        cost_price = float(request.POST.get('cost_price'))

        supplier = get_object_or_404(Supplier, id=supplier_id)
        part = get_object_or_404(SparePart, id=part_id)
        po_no = f"PO-{uuid.uuid4().hex[:6].upper()}"
        total_amount = quantity * cost_price

        with transaction.atomic():
            order = PurchaseOrder.objects.create(
                po_number=po_no,
                supplier=supplier,
                total_amount=total_amount,
                status='RECEIVED'
            )
            PurchaseOrderItem.objects.create(
                order=order,
                part=part,
                quantity=quantity,
                cost_price=cost_price
            )

        messages.success(request, f"Purchase Order '{po_no}' recorded. Stock increased by {quantity} units!")
        return redirect('purchase_list')

    suppliers = Supplier.objects.all()
    parts = SparePart.objects.all()

    # Agar koi supplier na ho toh dummy add karein
    if not suppliers.exists():
        Supplier.objects.create(name="Farooq Auto Importers", company_name="Farooq Autos Lahore", phone="0300-9876543")
        suppliers = Supplier.objects.all()

    return render(request, 'purchases/form.html', {
        'suppliers': suppliers,
        'parts': parts
    })