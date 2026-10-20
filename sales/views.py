import json
import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from inventory.models import SparePart
from .models import Sale, SaleItem


ZERO = Decimal('0.00')


@login_required
def pos_terminal_view(request):
    parts = list(
        SparePart.objects.filter(stock_quantity__gt=0).values(
            'id', 'name', 'part_number', 'brand', 'selling_price', 'stock_quantity'
        )
    )

    if request.method == 'POST':
        cart_data = request.POST.get('cart_data', '')
        try:
            cart_items = json.loads(cart_data)
        except (TypeError, json.JSONDecodeError):
            cart_items = None

        if not isinstance(cart_items, list) or not cart_items or len(cart_items) > 250:
            messages.error(request, 'The cart is invalid or empty. Please review the selected items.')
            return redirect('pos_terminal')

        quantities = {}
        for item in cart_items:
            if not isinstance(item, dict):
                messages.error(request, 'The cart contains an invalid item.')
                return redirect('pos_terminal')
            raw_id = item.get('id')
            raw_quantity = item.get('qty')
            try:
                part_id = int(raw_id)
                quantity = int(raw_quantity)
            except (TypeError, ValueError, OverflowError):
                messages.error(request, 'A cart item has an invalid product or quantity.')
                return redirect('pos_terminal')
            if isinstance(raw_id, bool) or isinstance(raw_quantity, bool) or quantity <= 0 or part_id in quantities:
                messages.error(request, 'A cart item has an invalid or duplicate quantity.')
                return redirect('pos_terminal')
            quantities[part_id] = quantity

        try:
            discount = Decimal(request.POST.get('discount', '0').strip())
        except (InvalidOperation, AttributeError):
            messages.error(request, 'Enter a valid discount amount.')
            return redirect('pos_terminal')
        if not discount.is_finite() or discount < ZERO:
            messages.error(request, 'The discount must be a non-negative amount.')
            return redirect('pos_terminal')
        if discount != discount.quantize(Decimal('0.01')):
            messages.error(request, 'Enter a discount with no more than two decimal places.')
            return redirect('pos_terminal')

        payment_method = request.POST.get('payment_method', 'CASH')
        if payment_method not in dict(Sale.PAYMENT_METHODS):
            messages.error(request, 'Select a valid payment method.')
            return redirect('pos_terminal')
        customer_name = (request.POST.get('customer_name') or '').strip() or 'Walk-in Customer'
        customer_phone = (request.POST.get('customer_phone') or '').strip()
        if len(customer_name) > 150 or len(customer_phone) > 20:
            messages.error(request, 'The customer name or phone number exceeds the allowed length.')
            return redirect('pos_terminal')

        with transaction.atomic():
            locked_parts = SparePart.objects.select_for_update().filter(
                pk__in=quantities
            ).in_bulk()
            if len(locked_parts) != len(quantities):
                messages.error(request, 'One or more selected parts are no longer available.')
                return redirect('pos_terminal')

            for part_id, quantity in quantities.items():
                if quantity > locked_parts[part_id].stock_quantity:
                    messages.error(
                        request,
                        f'Insufficient stock for {locked_parts[part_id].name}. '
                        f'Available quantity: {locked_parts[part_id].stock_quantity}.',
                    )
                    return redirect('pos_terminal')

            subtotal = sum(
                (
                    locked_parts[part_id].selling_price * quantity
                    for part_id, quantity in quantities.items()
                ),
                ZERO,
            )
            if discount > subtotal:
                messages.error(request, 'The discount cannot exceed the sale subtotal.')
                return redirect('pos_terminal')
            final_total = subtotal - discount
            invoice_no = f'POS-{uuid.uuid4().hex[:8].upper()}'
            sale = Sale.objects.create(
                sale_invoice_no=invoice_no,
                cashier=request.user,
                customer_name=customer_name,
                customer_phone=customer_phone,
                subtotal=subtotal,
                discount=discount,
                final_total=final_total,
                payment_method=payment_method,
            )
            for part_id, quantity in quantities.items():
                part = locked_parts[part_id]
                SaleItem.objects.create(
                    sale=sale,
                    part=part,
                    quantity=quantity,
                    unit_price=part.selling_price,
                    unit_cost=part.cost_price,
                    line_total=part.selling_price * quantity,
                )

        messages.success(request, f'Sale processed successfully. Receipt {invoice_no} is ready.')
        return redirect(
            f"{reverse('invoice_detail', kwargs={'invoice_no': sale.sale_invoice_no})}?print=1"
        )

    return render(request, 'sales/pos.html', {
        'parts': parts,
    })


@login_required
def sales_history_view(request):
    sales = Sale.objects.select_related('cashier').all().order_by('-created_at')
    return render(request, 'sales/history.html', {'sales': sales})
