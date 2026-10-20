from django.db import models


class InvoiceProfile(models.Model):
    LOGO_PLACEMENTS = (
        ('LEFT', 'Left'),
        ('CENTER', 'Center'),
        ('RIGHT', 'Right'),
    )
    LAYOUTS = (
        ('RECEIPT', 'Thermal receipt (80 mm)'),
        ('A4', 'Full-page invoice (A4)'),
    )

    legal_title = models.CharField(max_length=200, default='AutoPro ERP')
    contact_numbers = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=80, blank=True)
    physical_address = models.TextField(blank=True)
    footer_terms = models.TextField(blank=True, default='Thank you for your business.')
    logo = models.FileField(upload_to='invoice_logos/', blank=True)
    logo_placement = models.CharField(
        max_length=10, choices=LOGO_PLACEMENTS, default='CENTER'
    )
    layout = models.CharField(max_length=10, choices=LAYOUTS, default='RECEIPT')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Invoice profile'
        verbose_name_plural = 'Invoice profile'

    def __str__(self):
        return self.legal_title
