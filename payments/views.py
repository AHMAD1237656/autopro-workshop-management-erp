from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PaymentVoucher
from ledger.models import Account
import uuid

@login_required
def payment_list_view(request):
    vouchers = PaymentVoucher.objects.select_related('account').all().order_by('-created_at')
    return render(request, 'payments/list.html', {'vouchers': vouchers})

@login_required
def payment_create_view(request):
    if request.method == "POST":
        account_id = request.POST.get('account_id')
        voucher_type = request.POST.get('voucher_type')
        amount = float(request.POST.get('amount'))
        payment_mode = request.POST.get('payment_mode')
        reference_note = request.POST.get('reference_note')

        account = Account.objects.get(id=account_id)
        voucher_no = f"PV-{uuid.uuid4().hex[:6].upper()}"

        PaymentVoucher.objects.create(
            voucher_no=voucher_no,
            voucher_type=voucher_type,
            account=account,
            amount=amount,
            payment_mode=payment_mode,
            reference_note=reference_note
        )

        messages.success(request, f"Payment Voucher '{voucher_no}' recorded & ledger updated!")
        return redirect('payment_list')

    accounts = Account.objects.all()
    return render(request, 'payments/create.html', {'accounts': accounts})