from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from inventory.models import SparePart

class Vehicle(models.Model):
    registration_number = models.CharField(max_length=50, unique=True, help_text="Vehicle registration number")
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    make = models.CharField(max_length=100, help_text="Vehicle manufacturer")
    model_name = models.CharField(max_length=100, help_text="Vehicle model designation")
    year = models.PositiveIntegerField()
    mileage = models.PositiveIntegerField(help_text="Current odometer reading in kilometres")

    def __str__(self):
        return f"{self.registration_number} ({self.make} {self.model_name})"

class JobCard(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Inspection'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_PARTS', 'Waiting for Parts'),
        ('COMPLETED', 'Repair Completed'),
        ('DELIVERED', 'Delivered & Settled'),
    )

    job_number = models.CharField(max_length=50, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='job_cards')
    assigned_mechanic = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    complaint_description = models.TextField(help_text="Customer-reported concerns and inspection findings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    labor_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_cost(self):
        parts_cost = sum(item.total_price for item in self.parts_used.all())
        return parts_cost + self.labor_charges

    def __str__(self):
        return f"Job #{self.job_number} - {self.vehicle.registration_number}"

class JobCardItem(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='parts_used')
    part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    @property
    def total_price(self):
        return self.quantity * self.unit_price

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