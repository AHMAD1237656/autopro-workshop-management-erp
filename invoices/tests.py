from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InvoiceProfile


class InvoiceSettingsTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='invoice-manager', password='test-password')
        self.client.force_login(user)

    def test_settings_page_renders_and_persists_invoice_profile(self):
        response = self.client.get(reverse('invoice_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live invoice preview')

        response = self.client.post(reverse('invoice_settings'), {
            'legal_title': 'AutoPro Motor Services Ltd.',
            'contact_numbers': '+92 300 1234567',
            'tax_id': 'NTN-12345',
            'physical_address': 'Main Business Road',
            'footer_terms': 'Payment is due upon receipt.',
            'logo_placement': 'RIGHT',
            'layout': 'A4',
        })

        self.assertRedirects(response, reverse('invoice_settings'), fetch_redirect_response=False)
        profile = InvoiceProfile.objects.get(pk=1)
        self.assertEqual(profile.legal_title, 'AutoPro Motor Services Ltd.')
        self.assertEqual(profile.logo_placement, 'RIGHT')
        self.assertEqual(profile.layout, 'A4')

    def test_invalid_invoice_layout_is_rejected(self):
        response = self.client.post(reverse('invoice_settings'), {
            'legal_title': 'AutoPro',
            'logo_placement': 'CENTER',
            'layout': 'INVALID',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(InvoiceProfile.objects.get(pk=1).layout == 'INVALID')
        self.assertContains(response, 'Select a valid invoice layout.')
