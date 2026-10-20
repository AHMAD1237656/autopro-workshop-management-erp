from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class SparePart(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='parts')
    name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, unique=True, help_text="Original equipment manufacturer number or stock keeping unit")
    brand = models.CharField(max_length=100, help_text="Manufacturer or supplier brand")
    compatible_vehicles = models.CharField(max_length=255, help_text="Vehicle makes, models, and applicable model years")
    shelf_location = models.CharField(max_length=50, help_text="Warehouse rack, shelf, or bin location")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_alert = models.PositiveIntegerField(default=5, help_text="Low stock alert threshold")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_alert

    def __str__(self):
        return f"{self.name} ({self.part_number}) - Stock: {self.stock_quantity}"