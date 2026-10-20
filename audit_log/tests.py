from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from audit_log.models import ActivityLog
from audit_log.utils import reset_audit_context, set_audit_context
from ledger.models import Account
from payments.models import PaymentVoucher
from sales.models import Sale
from workshop.models import JobCard, Vehicle


class BusinessActivityAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='operator', password='test-password')

    def test_business_record_creation_is_audited_with_request_context(self):
        vehicle = Vehicle.objects.create(
            registration_number='AUD-100',
            customer_name='Jamie Lee',
            customer_phone='555-0101',
            make='Toyota',
            model_name='Corolla',
            year=2021,
            mileage=24000,
        )
        account = Account.objects.create(
            account_name='Cash Account',
            account_type='CASH',
            current_balance=Decimal('0.00'),
        )

        token = set_audit_context(self.user, '192.0.2.10')
        try:
            job = JobCard.objects.create(
                job_number='JC-AUDIT',
                vehicle=vehicle,
                complaint_description='Diagnostic check',
            )
            sale = Sale.objects.create(
                sale_invoice_no='POS-AUDIT',
                cashier=self.user,
                final_total=Decimal('25.00'),
            )
            voucher = PaymentVoucher.objects.create(
                voucher_no='PV-AUDIT',
                voucher_type='RECEIPT',
                account=account,
                amount=Decimal('25.00'),
                reference_note='Customer receipt',
            )
        finally:
            reset_audit_context(token)

        logs = ActivityLog.objects.filter(
            model_name__in=('workshop.JobCard', 'sales.Sale', 'payments.PaymentVoucher')
        )
        self.assertEqual(logs.count(), 3)
        for obj in (job, sale, voucher):
            entry = logs.get(object_repr=str(obj))
            self.assertEqual(entry.user, self.user)
            self.assertEqual(entry.ip_address, '192.0.2.10')

    def test_audit_trail_requires_authentication_and_lists_activity(self):
        ActivityLog.objects.create(
            user=self.user,
            action='Created',
            model_name='sales.Sale',
            object_repr='POS-200',
            ip_address='192.0.2.20',
        )
        response = self.client.get(reverse('audit_log'))
        self.assertRedirects(response, '/login/?next=/audit-log/')

        self.client.force_login(self.user)
        response = self.client.get(reverse('audit_log'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'POS-200')
