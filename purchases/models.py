from django.db import models
from inventory.models import SparePart

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=25)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} ({self.name})"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('RECEIVED', 'Received & Stock Updated'),
        ('PENDING', 'Pending Delivery'),
    )

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO #{self.po_number} - {self.supplier.company_name}"

class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.quantity * self.cost_price

    def save(self, *args, **kwargs):
        # Jab purchase item save ho toh inventory stock auto-increment ho
        if not self.pk:
            self.part.stock_quantity += self.quantity
            self.part.cost_price = self.cost_price
            self.part.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part.name} x {self.quantity}"