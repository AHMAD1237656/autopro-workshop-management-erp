from django.db import models
from ledger.models import Account, LedgerEntry

class PaymentVoucher(models.Model):
    VOUCHER_TYPES = (
        ('RECEIPT', 'Payment Received (Inflow)'),
        ('PAYMENT', 'Payment Made (Outflow)'),
    )

    PAYMENT_MODES = (
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('ONLINE', 'Bank Transfer / Online'),
    )

    voucher_no = models.CharField(max_length=50, unique=True)
    voucher_type = models.CharField(max_length=15, choices=VOUCHER_TYPES)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='vouchers')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=15, choices=PAYMENT_MODES, default='CASH')
    reference_note = models.CharField(max_length=200, help_text="Transaction reference or cheque number")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Jab payment voucher save ho toh auto ledger entry create ho
        if not self.pk:
            super().save(*args, **kwargs)
            is_receipt = self.voucher_type == 'RECEIPT'
            LedgerEntry.objects.create(
                account=self.account,
                transaction_type='CREDIT' if is_receipt else 'DEBIT',
                amount=self.amount,
                reference_no=self.voucher_no,
                description=f"Voucher payment settlement via {self.payment_mode}: {self.reference_note}"
            )
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.voucher_no} - {self.voucher_type} Rs. {self.amount}"