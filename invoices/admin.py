from django.contrib import admin
from .models import InvoiceProfile

@admin.register(InvoiceProfile)
class InvoiceProfileAdmin(admin.ModelAdmin):
    list_display = ('legal_title', 'layout', 'logo_placement', 'updated_at')
