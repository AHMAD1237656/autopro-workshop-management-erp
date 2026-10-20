from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('CUSTOMER', 'Customer Account (Receivable)'),
        ('SUPPLIER', 'Supplier Account (Payable)'),
        ('BANK', 'Bank Account'),
        ('CASH', 'Cash in Hand'),
        ('EXPENSE', 'Operating Expense'),
    )

    account_name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    contact_phone = models.CharField(max_length=25, blank=True, null=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="A positive balance is a debit; a negative balance is a credit.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()}) - Bal: Rs. {self.current_balance}"

class LedgerEntry(models.Model):
    TRANSACTION_TYPES = (
        ('DEBIT', 'Debit (+)'),
        ('CREDIT', 'Credit (-)'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_no = models.CharField(max_length=100, help_text="Invoice, purchase order, or receipt reference")
    description = models.TextField()
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.transaction_type not in dict(self.TRANSACTION_TYPES):
                raise ValidationError({'transaction_type': 'Select a valid transaction type.'})
            if self.amount <= 0:
                raise ValidationError({'amount': 'The transaction amount must be greater than zero.'})
            using = kwargs.get('using') or self._state.db
            with transaction.atomic(using=using):
                account = Account.objects.using(using).select_for_update().get(pk=self.account_id)
                current_balance = Decimal(account.current_balance)
                amount = Decimal(self.amount)
                if self.transaction_type == 'DEBIT':
                    current_balance += amount
                else:
                    current_balance -= amount
                account.current_balance = current_balance
                account.save(using=using, update_fields=('current_balance',))
                self.account = account
                self.balance_after_transaction = current_balance
                super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account.account_name} - {self.transaction_type} Rs. {self.amount}"


class OperatingExpense(models.Model):
    expense_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='operating_expenses'
    )
    payment_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='expense_payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    reference_no = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_expenses',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-expense_date', '-pk')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='operating_expense_amount_positive',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            super().save(*args, **kwargs)
            return
        if self.amount <= 0:
            raise ValidationError({'amount': 'The expense amount must be greater than zero.'})
        if self.expense_account.account_type != 'EXPENSE':
            raise ValidationError({'expense_account': 'Select an operating expense account.'})
        if self.payment_account.account_type not in {'CASH', 'BANK'}:
            raise ValidationError({'payment_account': 'Select a cash or bank account.'})
        with transaction.atomic():
            super().save(*args, **kwargs)
            LedgerEntry.objects.create(
                account=self.expense_account,
                transaction_type='DEBIT',
                amount=self.amount,
                reference_no=self.reference_no,
                description=self.description,
            )
            LedgerEntry.objects.create(
                account=self.payment_account,
                transaction_type='CREDIT',
                amount=self.amount,
                reference_no=self.reference_no,
                description=self.description,
            )

    def __str__(self):
        return f"{self.reference_no} - Rs. {self.amount}"