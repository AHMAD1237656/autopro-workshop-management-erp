from decimal import Decimal
import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import render
from django.utils import timezone

from inventory.models import SparePart
from ledger.models import OperatingExpense
from sales.models import Sale
from sales.models import SaleItem
from showroom.models import ShowroomVehicle
from workshop.models import JobCard, JobCardItem


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    selected_range = request.GET.get('range', '7')
    if selected_range not in {'7', '30', '90'}:
        selected_range = '7'
    range_days = int(selected_range)
    start_date = today - timedelta(days=range_days - 1)
    zero = Decimal('0.00')
    sales_today = Sale.objects.filter(created_at__date=today).aggregate(
        total=Coalesce(Sum('final_total'), zero, output_field=DecimalField())
    )['total']
    workshop_jobs_today = JobCard.objects.filter(created_at__date=today)
    labor_today = workshop_jobs_today.aggregate(
        total=Coalesce(Sum('labor_charges'), zero, output_field=DecimalField())
    )['total']
    parts_today = JobCardItem.objects.filter(
        job_card__created_at__date=today
    ).aggregate(
        total=Coalesce(
            Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
            zero,
            output_field=DecimalField(),
        )
    )['total']

    active_statuses = ('PENDING', 'IN_PROGRESS')
    active_jobs = JobCard.objects.filter(status__in=active_statuses)
    recent_jobs = active_jobs.select_related(
        'vehicle', 'assigned_mechanic'
    ).order_by('-created_at')[:5]
    recent_sales = Sale.objects.select_related('cashier').order_by('-created_at')[:5]
    low_stock_parts = SparePart.objects.filter(
        stock_quantity__lte=F('min_stock_alert')
    ).select_related('category').order_by('stock_quantity', 'name')[:5]

    sales_by_day = {
        row['day']: row
        for row in Sale.objects.filter(
            created_at__date__gte=start_date, created_at__date__lte=today
        ).annotate(day=TruncDate('created_at')).values('day').annotate(
            revenue=Coalesce(Sum('final_total'), zero, output_field=DecimalField()),
            transactions=Count('id'),
        )
    }
    jobs_by_day = {
        row['day']: row
        for row in JobCard.objects.filter(
            created_at__date__gte=start_date, created_at__date__lte=today,
            status__in=('COMPLETED', 'DELIVERED'),
        ).annotate(day=TruncDate('created_at')).values('day').annotate(
            labor=Coalesce(Sum('labor_charges'), zero, output_field=DecimalField()),
        )
    }
    parts_by_day = {
        row['day']: row['revenue']
        for row in JobCardItem.objects.filter(
            job_card__created_at__date__gte=start_date,
            job_card__created_at__date__lte=today,
            job_card__status__in=('COMPLETED', 'DELIVERED'),
        ).annotate(day=TruncDate('job_card__created_at')).values('day').annotate(
            revenue=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                zero,
                output_field=DecimalField(),
            ),
        )
    }
    pos_costs_by_day = {
        row['day']: row['cost']
        for row in SaleItem.objects.filter(
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=today,
        ).annotate(day=TruncDate('sale__created_at')).values('day').annotate(
            cost=Coalesce(
                Sum(
                    F('quantity') * Coalesce(
                        'unit_cost', 'part__cost_price', output_field=DecimalField()
                    ),
                    output_field=DecimalField(),
                ),
                zero,
                output_field=DecimalField(),
            ),
        )
    }
    workshop_costs_by_day = {
        row['day']: row['cost']
        for row in JobCardItem.objects.filter(
            job_card__created_at__date__gte=start_date,
            job_card__created_at__date__lte=today,
            job_card__status__in=('COMPLETED', 'DELIVERED'),
        ).annotate(day=TruncDate('job_card__created_at')).values('day').annotate(
            cost=Coalesce(
                Sum(
                    F('quantity') * Coalesce(
                        'unit_cost', 'part__cost_price', output_field=DecimalField()
                    ),
                    output_field=DecimalField(),
                ),
                zero,
                output_field=DecimalField(),
            ),
        )
    }
    expenses_by_day = {
        row['expense_date']: row['total']
        for row in OperatingExpense.objects.filter(
            expense_date__gte=start_date,
            expense_date__lte=today,
        ).values('expense_date').annotate(
            total=Coalesce(Sum('amount'), zero, output_field=DecimalField()),
        )
    }
    daily_series = []
    period_sales = Decimal('0.00')
    period_workshop_labor = Decimal('0.00')
    period_workshop_parts = Decimal('0.00')
    period_cogs = Decimal('0.00')
    period_expenses = Decimal('0.00')
    period_transactions = 0
    for day_offset in range(range_days):
        day = start_date + timedelta(days=day_offset)
        sales_row = sales_by_day.get(day, {})
        jobs_row = jobs_by_day.get(day, {})
        sales_revenue = sales_row.get('revenue', zero)
        workshop_labor = jobs_row.get('labor', zero)
        workshop_parts = parts_by_day.get(day, zero)
        cogs = pos_costs_by_day.get(day, zero) + workshop_costs_by_day.get(day, zero)
        expenses = expenses_by_day.get(day, zero)
        operating_profit = sales_revenue + workshop_labor + workshop_parts - cogs - expenses
        period_sales += sales_revenue
        period_workshop_labor += workshop_labor
        period_workshop_parts += workshop_parts
        period_cogs += cogs
        period_expenses += expenses
        period_transactions += sales_row.get('transactions', 0)
        daily_series.append({
            'date': day.strftime('%Y-%m-%d'),
            'sales': float(sales_revenue),
            'transactions': sales_row.get('transactions', 0),
            'workshop_labor': float(workshop_labor),
            'workshop_parts': float(workshop_parts),
            'workshop_revenue': float(workshop_labor + workshop_parts),
            'operating_profit': float(operating_profit),
        })
    period_revenue = period_sales + period_workshop_labor + period_workshop_parts
    period_gross_profit = period_revenue - period_cogs
    period_operating_profit = period_gross_profit - period_expenses

    return render(request, 'dashboard/index.html', {
        'today': today,
        'selected_range': selected_range,
        'range_days': range_days,
        'daily_series_json': json.dumps(daily_series, cls=DjangoJSONEncoder),
        'period_sales': period_sales,
        'period_workshop_revenue': period_workshop_labor + period_workshop_parts,
        'period_revenue': period_revenue,
        'period_transactions': period_transactions,
        'period_cogs': period_cogs,
        'period_gross_profit': period_gross_profit,
        'period_expenses': period_expenses,
        'period_operating_profit': period_operating_profit,
        'revenue_today': sales_today + labor_today + parts_today,
        'sales_today': sales_today,
        'workshop_revenue_today': labor_today + parts_today,
        'active_jobs_count': active_jobs.count(),
        'low_stock_count': SparePart.objects.filter(
            stock_quantity__lte=F('min_stock_alert')
        ).count(),
        'low_stock_parts': low_stock_parts,
        'available_vehicles_count': ShowroomVehicle.objects.filter(
            status='AVAILABLE'
        ).count(),
        'recent_jobs': recent_jobs,
        'recent_sales': recent_sales,
    })
