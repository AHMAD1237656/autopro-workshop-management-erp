from django.db import models

class ShowroomVehicle(models.Model):
    CONDITION_CHOICES = (
        ('NEW', 'Brand New'),
        ('USED', 'Pre-Owned / Used'),
    )
    
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available for Sale'),
        ('BOOKED', 'Booked / Token Paid'),
        ('SOLD', 'Sold & Delivered'),
    )

    vin_number = models.CharField(max_length=100, unique=True, help_text="VIN or Chassis Number")
    engine_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200, help_text="e.g., Honda Civic RS Turbo 2022")
    make = models.CharField(max_length=100, help_text="Honda, Toyota, Suzuki, etc.")
    model_name = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    mileage = models.PositiveIntegerField(help_text="Odometer reading in KM")
    color = models.CharField(max_length=50)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='USED')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    registration_status = models.CharField(max_length=100, default="Unregistered / Applied For")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.vin_number}) - {self.get_status_display()}"