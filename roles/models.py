from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    ROLE_CHOICES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('WORKSHOP_MANAGER', 'Workshop Manager'),
        ('MECHANIC', 'Mechanic Technician'),
        ('POS_CASHIER', 'POS Cashier'),
        ('SHOWROOM_AGENT', 'Showroom Sales Agent'),
    )
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'Unassigned'}"