from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Account, LedgerEntry, OperatingExpense


@login_required
def account_list_view(request):
    accounts = Account.objects.all().order_by('account_type', 'account_name')
    query = request.GET.get('q')
    type_filter = request.GET.get('type')

    if query:
        accounts = accounts.filter(account_name__icontains=query)
    if type_filter:
        accounts = accounts.filter(account_type=type_filter)

    zero = Decimal('0.00')
    balances = Account.objects.aggregate(
        receivables=Coalesce(
            Sum(
                Case(
                    When(account_type='CUSTOMER', current_balance__gt=zero, then='current_balance'),
                    default=Value(zero),
                    output_field=DecimalField(),
                )
            ),
            zero,
            output_field=DecimalField(),
        ),
        payables=Coalesce(
            Sum(
                Case(
                    When(
                        account_type='SUPPLIER',
                        current_balance__lt=zero,
                        then=F('current_balance') * -1,
                    ),
                    default=Value(zero),
                    output_field=DecimalField(),
                )
            ),
            zero,
            output_field=DecimalField(),
        ),
    )
    return render(request, 'ledger/list.html', {
        'accounts': accounts,
        'search_query': query or '',
        'selected_type': type_filter or '',
        **balances,
    })


@login_required
def account_statement_view(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    entries = account.entries.all().order_by('created_at', 'pk')
    return render(request, 'ledger/statement.html', {
        'account': account,
        'entries': entries
    })


@login_required
def account_create_view(request):
    if request.method == "POST":
        name = request.POST.get('account_name', '').strip()
        account_type = request.POST.get('account_type')
        phone = request.POST.get('contact_phone', '').strip()
        try:
            opening_balance = Decimal(request.POST.get('opening_balance') or '0')
        except InvalidOperation:
            messages.error(request, 'Enter a valid opening balance.')
            return render(request, 'ledger/form.html')
        if not name or account_type not in dict(Account.ACCOUNT_TYPES):
            messages.error(request, 'Enter an account name and select a valid account type.')
            return render(request, 'ledger/form.html')
        if not opening_balance.is_finite():
            messages.error(request, 'Enter a finite opening balance.')
            return render(request, 'ledger/form.html')

        with transaction.atomic():
            acc = Account.objects.create(
                account_name=name,
                account_type=account_type,
                contact_phone=phone,
                current_balance=Decimal('0.00'),
            )
            if opening_balance != 0:
                LedgerEntry.objects.create(
                    account=acc,
                    transaction_type='DEBIT' if opening_balance > 0 else 'CREDIT',
                    amount=abs(opening_balance),
                    reference_no='OP-BAL',
                    description='Opening account balance entry',
                )

        messages.success(request, f"Account '{name}' was created successfully.")
        return redirect('account_list')

    return render(request, 'ledger/form.html')


def _expense_form_context():
    return {
        'expense_accounts': Account.objects.filter(account_type='EXPENSE').order_by('account_name'),
        'payment_accounts': Account.objects.filter(
            account_type__in=('CASH', 'BANK')
        ).order_by('account_name'),
        'today': timezone.localdate(),
    }


@login_required
def expense_list_view(request):
    expenses = OperatingExpense.objects.select_related(
        'expense_account', 'payment_account', 'recorded_by'
    )
    return render(request, 'ledger/expenses.html', {
        'expenses': expenses,
        'expense_total': expenses.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total'],
    })


@login_required
def expense_create_view(request):
    context = _expense_form_context()
    if request.method == 'POST':
        raw_amount = request.POST.get('amount', '').strip()
        raw_date = request.POST.get('expense_date', '').strip()
        expense_account_id = request.POST.get('expense_account')
        payment_account_id = request.POST.get('payment_account')
        reference_no = request.POST.get('reference_no', '').strip()
        description = request.POST.get('description', '').strip()

        try:
            amount = Decimal(raw_amount)
            amount_valid = (
                amount.is_finite()
                and Decimal('0.00') < amount < Decimal('10000000000.00')
                and amount == amount.quantize(Decimal('0.01'))
            )
        except InvalidOperation:
            amount = Decimal('0.00')
            amount_valid = False
        try:
            expense_date = date.fromisoformat(raw_date)
        except ValueError:
            expense_date = None

        if not amount_valid:
            messages.error(request, 'Enter an expense amount greater than zero with no more than two decimal places.')
        elif expense_date is None:
            messages.error(request, 'Enter a valid expense date.')
        elif not reference_no or len(reference_no) > 80:
            messages.error(request, 'Enter a reference of no more than 80 characters.')
        elif not description or len(description) > 255:
            messages.error(request, 'Enter a description of no more than 255 characters.')
        elif not (expense_account_id or '').isdigit() or not (payment_account_id or '').isdigit():
            messages.error(request, 'Select valid expense and payment accounts.')
        else:
            expense_account = Account.objects.filter(
                pk=expense_account_id, account_type='EXPENSE'
            ).first()
            payment_account = Account.objects.filter(
                pk=payment_account_id, account_type__in=('CASH', 'BANK')
            ).first()
            if not expense_account or not payment_account:
                messages.error(request, 'Select a valid operating expense and cash or bank account.')
            elif OperatingExpense.objects.filter(reference_no=reference_no).exists():
                messages.error(request, 'That expense reference is already in use.')
            else:
                try:
                    with transaction.atomic():
                        OperatingExpense.objects.create(
                            expense_account=expense_account,
                            payment_account=payment_account,
                            amount=amount,
                            expense_date=expense_date,
                            reference_no=reference_no,
                            description=description,
                            recorded_by=request.user,
                        )
                except IntegrityError:
                    messages.error(request, 'That expense reference is already in use.')
                    return render(request, 'ledger/expense_form.html', context)
                messages.success(request, 'The expense was recorded and posted to both ledger accounts.')
                return redirect('expense_list')

    return render(request, 'ledger/expense_form.html', context)