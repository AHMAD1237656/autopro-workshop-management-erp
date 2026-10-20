from decimal import Decimal
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Category, SparePart
from ledger.models import Account, OperatingExpense
from sales.models import Sale, SaleItem
from showroom.models import ShowroomVehicle
from workshop.models import JobCard, JobCardItem, Vehicle


class ExecutiveDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='manager', password='test-password')
        self.client.force_login(self.user)

        category = Category.objects.create(name='Engine')
        self.part = SparePart.objects.create(
            category=category,
            name='Oil Filter',
            part_number='OF-100',
            brand='AutoPro',
            compatible_vehicles='Sedan',
            shelf_location='A-01',
            cost_price=Decimal('10.00'),
            selling_price=Decimal('20.00'),
            stock_quantity=5,
            min_stock_alert=5,
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='ABC-123',
            customer_name='Alex Morgan',
            customer_phone='555-0100',
            make='Honda',
            model_name='Civic',
            year=2022,
            mileage=12000,
        )
        self.job = JobCard.objects.create(
            job_number='JC-100',
            vehicle=self.vehicle,
            assigned_mechanic=self.user,
            complaint_description='Routine inspection',
            status='IN_PROGRESS',
            labor_charges=Decimal('50.00'),
        )
        JobCardItem.objects.create(
            job_card=self.job,
            part=self.part,
            quantity=2,
            unit_price=Decimal('15.00'),
        )
        Sale.objects.create(
            sale_invoice_no='POS-100',
            cashier=self.user,
            customer_name='Walk-in Customer',
            subtotal=Decimal('100.00'),
            final_total=Decimal('100.00'),
        )
        ShowroomVehicle.objects.create(
            vin_number='VIN-100',
            engine_number='ENG-100',
            title='Honda Civic',
            make='Honda',
            model_name='Civic',
            year=2022,
            mileage=0,
            color='Black',
            condition='NEW',
            status='AVAILABLE',
            purchase_cost=Decimal('10000.00'),
            selling_price=Decimal('12000.00'),
        )

    def test_dashboard_shows_live_metrics_and_recent_records(self):
        response = self.client.get(reverse('dashboard_home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['revenue_today'], Decimal('180.00'))
        self.assertEqual(response.context['active_jobs_count'], 1)
        self.assertEqual(response.context['low_stock_count'], 1)
        self.assertEqual(response.context['available_vehicles_count'], 1)
        self.assertContains(response, 'JC-100')
        self.assertContains(response, 'POS-100')

    def test_dashboard_alias_and_unauthenticated_root(self):
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        self.client.logout()
        response = self.client.get('/')
        self.assertRedirects(response, '/login/?next=/')

    def test_dashboard_chart_series_has_serializable_zero_value_days(self):
        Sale.objects.all().delete()

        response = self.client.get(reverse('dashboard_home'), {'range': '7'})

        self.assertEqual(response.status_code, 200)
        daily_series = json.loads(response.context['daily_series_json'])
        self.assertEqual(len(daily_series), 7)
        self.assertTrue(all(day['transactions'] == 0 for day in daily_series))
        self.assertTrue(all(day['sales'] == 0 for day in daily_series))
        self.assertTrue(all(len(day['date']) == 10 for day in daily_series))
        self.assertContains(response, 'id="revenueChart"')
        self.assertContains(response, 'id="transactionsChart"')

    def test_reports_render_all_analytical_tabs(self):
        completed_job = JobCard.objects.create(
            job_number='JC-101',
            vehicle=self.vehicle,
            assigned_mechanic=self.user,
            complaint_description='Brake service',
            status='COMPLETED',
            labor_charges=Decimal('80.00'),
        )
        JobCardItem.objects.create(
            job_card=completed_job,
            part=self.part,
            quantity=1,
            unit_price=Decimal('15.00'),
        )

        revenue = self.client.get(reverse('reports'))
        self.assertEqual(revenue.status_code, 200)
        self.assertEqual(revenue.context['total_revenue'], Decimal('195.00'))

        technicians = self.client.get(reverse('reports'), {'tab': 'technicians'})
        self.assertEqual(technicians.status_code, 200)
        self.assertEqual(technicians.context['completed_job_count'], 1)
        self.assertEqual(technicians.context['total_labor_revenue'], Decimal('80.00'))

        inventory = self.client.get(reverse('reports'), {'tab': 'inventory'})
        self.assertEqual(inventory.status_code, 200)
        self.assertEqual(inventory.context['cost_value'], Decimal('20.00'))
        self.assertEqual(inventory.context['selling_value'], Decimal('40.00'))

    def test_dashboard_operating_profit_includes_cost_of_goods_and_expenses(self):
        self.part.stock_quantity = 10
        self.part.save(update_fields=('stock_quantity',))
        sale = Sale.objects.get(sale_invoice_no='POS-100')
        SaleItem.objects.create(
            sale=sale,
            part=self.part,
            quantity=2,
            unit_price=Decimal('50.00'),
            line_total=Decimal('100.00'),
        )
        completed_job = JobCard.objects.create(
            job_number='JC-PNL',
            vehicle=self.vehicle,
            assigned_mechanic=self.user,
            complaint_description='Completed service',
            status='COMPLETED',
            labor_charges=Decimal('50.00'),
        )
        JobCardItem.objects.create(
            job_card=completed_job,
            part=self.part,
            quantity=2,
            unit_price=Decimal('15.00'),
        )
        expense_account = Account.objects.create(
            account_name='Workshop utilities',
            account_type='EXPENSE',
        )
        cash_account = Account.objects.create(
            account_name='Petty cash',
            account_type='CASH',
            current_balance=Decimal('500.00'),
        )
        OperatingExpense.objects.create(
            expense_account=expense_account,
            payment_account=cash_account,
            amount=Decimal('15.00'),
            expense_date=timezone.localdate(),
            reference_no='EXP-15',
            description='Workshop supplies',
            recorded_by=self.user,
        )

        response = self.client.get(reverse('dashboard_home'), {'range': '7'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['period_revenue'], Decimal('180.00'))
        self.assertEqual(response.context['period_cogs'], Decimal('40.00'))
        self.assertEqual(response.context['period_expenses'], Decimal('15.00'))
        self.assertEqual(response.context['period_operating_profit'], Decimal('125.00'))
