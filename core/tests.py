"""
Core service tests.
"""
from django.test import TestCase
from django.core.management import call_command

from core.models import Product, StockMovement
from core.services import deduct_stock, restore_stock
from master_data.models import ProductCategory, UnitOfMeasure


class StockServiceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('setup_master_data')

    def setUp(self):
        cat = ProductCategory.objects.first()
        unit = UnitOfMeasure.objects.first()
        self.product = Product.objects.create(
            name='Test', sku='T1', category=cat, unit=unit,
            stock_quantity=50, low_stock_threshold=10
        )

    def test_deduct_stock(self):
        deduct_stock(self.product.id, 10, 'Test', 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 40)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_restore_stock(self):
        restore_stock(self.product.id, 5, 'Test', 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 55)
