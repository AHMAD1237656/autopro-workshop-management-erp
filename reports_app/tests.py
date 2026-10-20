from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from inventory.models import Category, SparePart
from ledger.models import Account, LedgerEntry, OperatingExpense
from sales.models import Sale


class ReportExportTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='report-manager', password='test-password')
        self.client.force_login(user)
        category = Category.objects.create(name='Electrical')
        self.part = SparePart.objects.create(
            category=category,
            name='Ignition Coil',
            part_number='IC-101',
            brand='AutoPro',
            compatible_vehicles='Passenger vehicles',
            shelf_location='B-02',
            cost_price=Decimal('12.00'),
            selling_price=Decimal('20.00'),
            stock_quantity=3,
        )
        Sale.objects.create(
            sale_invoice_no='POS-REPORT-1',
            cashier=user,
            customer_name='Retail Customer',
            subtotal=Decimal('20.00'),
            final_total=Decimal('20.00'),
        )

    def test_daily_sales_csv_contains_report_heading_and_sale(self):
        response = self.client.get(reverse('reports'), {'export': 'sales'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        content = response.content.decode('utf-8-sig')
        self.assertIn('daily-pos-sales', content)
        self.assertIn('POS-REPORT-1', content)

    def test_stock_valuation_csv_contains_computed_values(self):
        response = self.client.get(reverse('reports'), {'export': 'inventory'})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Ignition Coil', content)
        self.assertIn('36.00', content)
        self.assertIn('60.00', content)

    def test_ledger_csv_requires_an_account_and_exports_running_balance(self):
        response = self.client.get(reverse('reports'), {'export': 'ledger'})
        self.assertEqual(response.status_code, 400)

        account = Account.objects.create(
            account_name='Fleet Customer',
            account_type='CUSTOMER',
        )
        LedgerEntry.objects.create(
            account=account,
            transaction_type='DEBIT',
            amount=Decimal('125.00'),
            reference_no='INV-125',
            description='Invoice charge',
        )
        response = self.client.get(reverse('reports'), {
            'export': 'ledger',
            'account_id': account.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('INV-125', response.content.decode('utf-8-sig'))
        self.assertIn('125.00', response.content.decode('utf-8-sig'))

    def test_operating_expense_csv_exports_posted_expenses(self):
        expense_account = Account.objects.create(
            account_name='Utilities Expense',
            account_type='EXPENSE',
        )
        cash_account = Account.objects.create(
            account_name='Petty Cash',
            account_type='CASH',
        )
        OperatingExpense.objects.create(
            expense_account=expense_account,
            payment_account=cash_account,
            amount=Decimal('45.00'),
            expense_date=Sale.objects.get().created_at.date(),
            reference_no='UTIL-CSV',
            description='Electricity bill',
        )

        response = self.client.get(reverse('reports'), {'export': 'expenses'})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('UTIL-CSV', content)
        self.assertIn('Electricity bill', content)
        self.assertIn('45.00', content)
