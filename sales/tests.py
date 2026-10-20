import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from inventory.models import Category, SparePart
from .models import Sale, SaleItem


class PointOfSaleCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cashier', password='test-password')
        self.client.force_login(self.user)
        category = Category.objects.create(name='Filters')
        self.part = SparePart.objects.create(
            category=category,
            name='Oil Filter',
            part_number='OF-100',
            brand='AutoPro',
            compatible_vehicles='Passenger vehicles',
            shelf_location='A-01',
            cost_price=Decimal('10.00'),
            selling_price=Decimal('20.00'),
            stock_quantity=4,
            min_stock_alert=1,
        )

    def post_cart(self, items, discount='0.00'):
        return self.client.post(reverse('pos_terminal'), {
            'cart_data': json.dumps(items),
            'discount': discount,
            'payment_method': 'CASH',
        })

    def test_checkout_uses_database_price_and_decrements_stock(self):
        response = self.post_cart([{'id': self.part.pk, 'qty': 2, 'price': '0.01'}])

        sale = Sale.objects.get()
        self.assertRedirects(
            response,
            reverse('invoice_detail', kwargs={'invoice_no': sale.sale_invoice_no}) + '?print=1',
            fetch_redirect_response=False,
        )
        sale_item = SaleItem.objects.get(sale=sale)
        self.assertEqual(sale.subtotal, Decimal('40.00'))
        self.assertEqual(sale.final_total, Decimal('40.00'))
        self.assertEqual(sale_item.unit_price, Decimal('20.00'))
        self.assertEqual(sale_item.unit_cost, Decimal('10.00'))
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_quantity, 2)

    def test_checkout_rejects_quantities_above_available_stock(self):
        response = self.post_cart([{'id': self.part.pk, 'qty': 5}])

        self.assertRedirects(response, reverse('pos_terminal'), fetch_redirect_response=False)
        self.assertFalse(Sale.objects.exists())
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_quantity, 4)

    def test_checkout_rejects_discount_above_subtotal(self):
        response = self.post_cart([{'id': self.part.pk, 'qty': 1}], discount='20.01')

        self.assertRedirects(response, reverse('pos_terminal'), fetch_redirect_response=False)
        self.assertFalse(Sale.objects.exists())
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_quantity, 4)

    def test_checkout_handles_malformed_cart_without_creating_sale(self):
        response = self.client.post(reverse('pos_terminal'), {'cart_data': '{invalid'})

        self.assertRedirects(response, reverse('pos_terminal'), fetch_redirect_response=False)
        self.assertFalse(Sale.objects.exists())
