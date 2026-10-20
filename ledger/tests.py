from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Account, LedgerEntry, OperatingExpense


class PartyLedgerViewTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='ledger-manager', password='test-password')
        self.client.force_login(user)

    def test_account_list_shows_receivables_and_payables(self):
        Account.objects.create(
            account_name='Customer Account',
            account_type='CUSTOMER',
            current_balance=Decimal('150.00'),
        )
        Account.objects.create(
            account_name='Supplier Account',
            account_type='SUPPLIER',
            current_balance=Decimal('-75.00'),
        )

        response = self.client.get(reverse('account_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['receivables'], Decimal('150.00'))
        self.assertEqual(response.context['payables'], Decimal('75.00'))

    def test_account_statement_lists_transactions_in_date_order(self):
        account = Account.objects.create(
            account_name='Customer Account',
            account_type='CUSTOMER',
        )
        first_entry = LedgerEntry.objects.create(
            account=account,
            transaction_type='DEBIT',
            amount=Decimal('100.00'),
            reference_no='INV-001',
            description='First invoice',
        )
        second_entry = LedgerEntry.objects.create(
            account=account,
            transaction_type='CREDIT',
            amount=Decimal('25.00'),
            reference_no='RCPT-001',
            description='Payment received',
        )

        response = self.client.get(
            reverse('account_statement', kwargs={'account_id': account.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['entries'].values_list('pk', flat=True)),
            [first_entry.pk, second_entry.pk],
        )
        self.assertContains(response, 'INV-001')
        self.assertContains(response, 'RCPT-001')

    def test_opening_balance_is_posted_exactly_once(self):
        response = self.client.post(reverse('account_create'), {
            'account_name': 'Opening Balance Customer',
            'account_type': 'CUSTOMER',
            'contact_phone': '',
            'opening_balance': '250.00',
        })

        self.assertRedirects(response, reverse('account_list'), fetch_redirect_response=False)
        account = Account.objects.get(account_name='Opening Balance Customer')
        self.assertEqual(account.current_balance, Decimal('250.00'))
        self.assertEqual(account.entries.count(), 1)
        self.assertEqual(account.entries.get().balance_after_transaction, Decimal('250.00'))

    def test_operating_expense_creates_balanced_debit_and_credit_entries(self):
        expense_account = Account.objects.create(
            account_name='Utilities Expense',
            account_type='EXPENSE',
        )
        cash_account = Account.objects.create(
            account_name='Petty Cash',
            account_type='CASH',
            current_balance=Decimal('200.00'),
        )

        expense = OperatingExpense.objects.create(
            expense_account=expense_account,
            payment_account=cash_account,
            amount=Decimal('75.00'),
            expense_date=timezone.localdate(),
            reference_no='UTIL-75',
            description='Monthly utilities',
            recorded_by=User.objects.get(username='ledger-manager'),
        )

        expense_account.refresh_from_db()
        cash_account.refresh_from_db()
        entries = list(LedgerEntry.objects.filter(reference_no=expense.reference_no))
        self.assertEqual(expense_account.current_balance, Decimal('75.00'))
        self.assertEqual(cash_account.current_balance, Decimal('125.00'))
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            sum(
                (entry.amount if entry.transaction_type == 'DEBIT' else -entry.amount)
                for entry in entries
            ),
            Decimal('0.00'),
        )

    def test_expense_form_records_a_valid_expense(self):
        expense_account = Account.objects.create(
            account_name='Workshop Supplies',
            account_type='EXPENSE',
        )
        cash_account = Account.objects.create(
            account_name='Workshop Cash',
            account_type='CASH',
            current_balance=Decimal('100.00'),
        )

        response = self.client.post(reverse('expense_create'), {
            'expense_date': timezone.localdate().isoformat(),
            'reference_no': 'SUP-001',
            'expense_account': expense_account.pk,
            'payment_account': cash_account.pk,
            'amount': '25.00',
            'description': 'Cleaning materials',
        })

        self.assertRedirects(response, reverse('expense_list'), fetch_redirect_response=False)
        self.assertTrue(OperatingExpense.objects.filter(reference_no='SUP-001').exists())
        self.assertEqual(
            LedgerEntry.objects.filter(reference_no='SUP-001').count(),
            2,
        )
