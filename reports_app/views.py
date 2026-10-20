import csv
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from inventory.models import SparePart
from ledger.models import Account, OperatingExpense
from sales.models import Sale
from workshop.models import JobCard, JobCardItem


COMPLETED_STATUSES = ('COMPLETED', 'DELIVERED')
ZERO_AMOUNT = Decimal('0.00')


def _safe_csv_cell(value):
    text = str(value if value is not None else '')
    if isinstance(value, str) and text.startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + text
    return text


def _csv_response(report_name, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{report_name}-{timezone.localdate():%Y%m%d}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([f'AutoPro ERP — {report_name}', f'Generated: {timezone.localtime():%Y-%m-%d %H:%M:%S %Z}'])
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe_csv_cell(value) for value in row])
    return response


def _export_report(request, export_type):
    if export_type == 'sales':
        today = timezone.localdate()
        sales = list(Sale.objects.filter(created_at__date=today).order_by('created_at'))
        subtotal = sum((sale.subtotal for sale in sales), ZERO_AMOUNT)
        discount_total = sum((sale.discount for sale in sales), ZERO_AMOUNT)
        revenue_total = sum((sale.final_total for sale in sales), ZERO_AMOUNT)
        rows = [
            (sale.created_at, sale.sale_invoice_no, sale.customer_name, sale.customer_phone,
             sale.get_payment_method_display(), sale.subtotal, sale.discount, sale.final_total)
            for sale in sales
        ]
        rows.append(('', '', 'TOTAL', '', '', subtotal, discount_total, revenue_total))
        return _csv_response('daily-pos-sales', (
            'Date and time', 'Invoice number', 'Customer', 'Phone',
            'Payment method', 'Subtotal', 'Discount', 'Total',
        ), rows)
    if export_type == 'inventory':
        parts = list(SparePart.objects.select_related('category').order_by('name'))
        units_total = sum(part.stock_quantity for part in parts)
        cost_total = sum(
            (part.cost_price * part.stock_quantity for part in parts), ZERO_AMOUNT
        )
        retail_total = sum(
            (part.selling_price * part.stock_quantity for part in parts), ZERO_AMOUNT
        )
        rows = [
            (part.name, part.part_number, part.brand, part.category.name, part.stock_quantity,
             part.cost_price, part.cost_price * part.stock_quantity,
             part.selling_price, part.selling_price * part.stock_quantity)
            for part in parts
        ]
        rows.append(('', '', '', 'TOTAL', units_total, '', cost_total, '', retail_total))
        return _csv_response('stock-valuation', (
            'Part name', 'SKU', 'Brand', 'Category', 'Quantity', 'Unit cost',
            'Cost value', 'Unit selling price', 'Retail value',
        ), rows)
    if export_type == 'technicians':
        technicians = list(User.objects.annotate(
            completed_jobs=Count(
                'assigned_jobs',
                filter=Q(assigned_jobs__status__in=COMPLETED_STATUSES),
                distinct=True,
            ),
            labor_revenue=Coalesce(
                Sum(
                    'assigned_jobs__labor_charges',
                    filter=Q(assigned_jobs__status__in=COMPLETED_STATUSES),
                    output_field=DecimalField(),
                ),
                Value(ZERO_AMOUNT, output_field=DecimalField()),
            ),
        ).filter(completed_jobs__gt=0).order_by('-labor_revenue', 'username'))
        total_jobs = sum(technician.completed_jobs for technician in technicians)
        total_labor = sum(
            (technician.labor_revenue for technician in technicians), ZERO_AMOUNT
        )
        rows = [
            (technician.get_full_name() or technician.username,
             technician.completed_jobs, technician.labor_revenue)
            for technician in technicians
        ]
        rows.append(('TOTAL', total_jobs, total_labor))
        return _csv_response('technician-efficiency', (
            'Technician', 'Completed jobs', 'Labor revenue',
        ), rows)
    if export_type == 'ledger':
        account_id = request.GET.get('account_id')
        if not account_id or not account_id.isdigit():
            return HttpResponse('A valid account_id is required for a ledger export.', status=400)
        account = get_object_or_404(Account, pk=account_id)
        running_balance = Decimal('0.00')
        rows = []
        for entry in account.entries.order_by('created_at', 'pk'):
            amount = entry.amount
            running_balance += amount if entry.transaction_type == 'DEBIT' else -amount
            rows.append((
                entry.created_at, entry.reference_no, entry.description,
                amount if entry.transaction_type == 'DEBIT' else '',
                amount if entry.transaction_type == 'CREDIT' else '',
                running_balance,
            ))
        rows.append(('', '', 'CLOSING BALANCE', '', '', running_balance))
        return _csv_response(f'party-ledger-{account.pk}', (
            'Date and time', 'Reference', 'Remarks', 'Debit', 'Credit', 'Balance',
        ), rows)
    if export_type == 'expenses':
        expenses = list(OperatingExpense.objects.select_related(
            'expense_account', 'payment_account', 'recorded_by'
        ))
        total_expenses = sum((expense.amount for expense in expenses), ZERO_AMOUNT)
        rows = [
            (expense.expense_date, expense.reference_no, expense.description,
             expense.expense_account.account_name, expense.payment_account.account_name,
             expense.recorded_by.get_full_name() or expense.recorded_by.username
             if expense.recorded_by else 'System', expense.amount)
            for expense in expenses
        ]
        rows.append(('', '', 'TOTAL', '', '', '', total_expenses))
        return _csv_response('operating-expenses', (
            'Expense date', 'Reference', 'Description', 'Expense account',
            'Payment account', 'Recorded by', 'Amount',
        ), rows)
    return HttpResponse('The requested export type is not supported.', status=400)


@login_required
def reports_view(request):
    export_type = request.GET.get('export')
    if export_type:
        return _export_report(request, export_type)

    selected_tab = request.GET.get('tab', 'revenue')
    if selected_tab not in {'revenue', 'technicians', 'inventory'}:
        selected_tab = 'revenue'

    context = {
        'selected_tab': selected_tab,
        'generated_at': timezone.localtime(),
    }

    if selected_tab == 'revenue':
        pos_totals = Sale.objects.aggregate(
            transaction_count=Count('id'),
            revenue=Coalesce(Sum('final_total'), ZERO_AMOUNT, output_field=DecimalField()),
        )
        completed_jobs = JobCard.objects.filter(status__in=COMPLETED_STATUSES)
        workshop_totals = completed_jobs.aggregate(
            labor_revenue=Coalesce(
                Sum('labor_charges'), ZERO_AMOUNT, output_field=DecimalField()
            ),
            job_count=Count('id'),
        )
        parts_revenue = JobCardItem.objects.filter(
            job_card__status__in=COMPLETED_STATUSES
        ).aggregate(
            total=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                ZERO_AMOUNT,
                output_field=DecimalField(),
            )
        )['total']
        total_revenue = (
            pos_totals['revenue'] + workshop_totals['labor_revenue'] + parts_revenue
        )
        context.update({
            'pos_transaction_count': pos_totals['transaction_count'],
            'pos_revenue': pos_totals['revenue'],
            'workshop_job_count': workshop_totals['job_count'],
            'workshop_labor_revenue': workshop_totals['labor_revenue'],
            'workshop_parts_revenue': parts_revenue,
            'workshop_revenue': workshop_totals['labor_revenue'] + parts_revenue,
            'total_revenue': total_revenue,
            'pos_revenue_share': (
                pos_totals['revenue'] / total_revenue * 100 if total_revenue else 0
            ),
            'labor_revenue_share': (
                workshop_totals['labor_revenue'] / total_revenue * 100
                if total_revenue else 0
            ),
            'parts_revenue_share': (
                parts_revenue / total_revenue * 100 if total_revenue else 0
            ),
        })

    elif selected_tab == 'technicians':
        technicians = list(
            User.objects.annotate(
                completed_jobs=Count(
                    'assigned_jobs',
                    filter=Q(assigned_jobs__status__in=COMPLETED_STATUSES),
                    distinct=True,
                ),
                labor_revenue=Coalesce(
                    Sum(
                        'assigned_jobs__labor_charges',
                        filter=Q(assigned_jobs__status__in=COMPLETED_STATUSES),
                        output_field=DecimalField(),
                    ),
                    Value(ZERO_AMOUNT, output_field=DecimalField()),
                ),
            ).filter(completed_jobs__gt=0).order_by('-labor_revenue', 'username')
        )
        total_jobs = sum(technician.completed_jobs for technician in technicians)
        total_labor_revenue = sum(
            (technician.labor_revenue for technician in technicians), ZERO_AMOUNT
        )
        context.update({
            'technicians': [
                {
                    'name': technician.get_full_name() or technician.username,
                    'completed_jobs': technician.completed_jobs,
                    'labor_revenue': technician.labor_revenue,
                    'job_share': (
                        technician.completed_jobs / total_jobs * 100 if total_jobs else 0
                    ),
                    'labor_share': (
                        technician.labor_revenue / total_labor_revenue * 100
                        if total_labor_revenue else 0
                    ),
                }
                for technician in technicians
            ],
            'completed_job_count': total_jobs,
            'total_labor_revenue': total_labor_revenue,
        })

    else:
        valuations = SparePart.objects.aggregate(
            total_units=Coalesce(Sum('stock_quantity'), 0),
            cost_value=Coalesce(
                Sum(
                    F('stock_quantity') * F('cost_price'),
                    output_field=DecimalField(),
                ),
                ZERO_AMOUNT,
                output_field=DecimalField(),
            ),
            selling_value=Coalesce(
                Sum(
                    F('stock_quantity') * F('selling_price'),
                    output_field=DecimalField(),
                ),
                ZERO_AMOUNT,
                output_field=DecimalField(),
            ),
        )
        stock_difference = valuations['selling_value'] - valuations['cost_value']
        markup_percentage = (
            stock_difference / valuations['cost_value'] * 100
            if valuations['cost_value'] else ZERO_AMOUNT
        )
        context.update({
            'total_units': valuations['total_units'],
            'cost_value': valuations['cost_value'],
            'selling_value': valuations['selling_value'],
            'stock_difference': stock_difference,
            'markup_percentage': markup_percentage,
            'low_stock_parts': SparePart.objects.filter(
                stock_quantity__lte=F('min_stock_alert')
            ).select_related('category').order_by('stock_quantity', 'name'),
        })

    return render(request, 'reports_app/index.html', context)
