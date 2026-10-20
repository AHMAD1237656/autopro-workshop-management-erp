from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from inventory.models import SparePart

class Sale(models.Model):
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('ONLINE', 'Bank Transfer / Online'),
    )

    sale_invoice_no = models.CharField(max_length=50, unique=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=150, default="Walk-in Customer")
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    final_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sale_invoice_no} - {self.customer_name} (Rs. {self.final_total})"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:
            using = kwargs.get('using') or self._state.db
            with transaction.atomic(using=using):
                part = SparePart.objects.using(using).select_for_update().get(pk=self.part_id)
                if self.quantity <= 0 or self.quantity > part.stock_quantity:
                    raise ValidationError(
                        {'quantity': f'Insufficient stock for {part.name}.'}
                    )
                if self.unit_cost is None:
                    self.unit_cost = part.cost_price
                part.stock_quantity -= self.quantity
                part.save(using=using, update_fields=('stock_quantity',))
                self.part = part
                super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part.name} x {self.quantity}"