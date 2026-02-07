from decimal import Decimal
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from purchasing.models import PurchaseOrder, PurchaseItem
from purchasing.services import create_purchase_order, receive_purchase_items
from core.models import Product, ProductCategory, UnitOfMeasure
from master_data.models import Supplier
from master_data.constants import PURCHASE_PENDING, PURCHASE_RECEIVED, PURCHASE_ORDERED

User = get_user_model()

class PurchasingServiceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('setup_master_data')

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.supplier = Supplier.objects.create(
            code="SUP001",
            name_en="Test Supplier",
            phone="09111111111"
        )
        
        # Setup Product
        cat = ProductCategory.objects.first()
        unit = UnitOfMeasure.objects.first()
        self.product = Product.objects.create(
            name="Test Product",
            category=cat,
            unit=unit,
            base_price=1000,
            stock_quantity=0  # Start with 0 stock
        )

    def test_create_purchase_order(self):
        """Test creating a PO via service."""
        items = [
            (self.product.id, 10, Decimal('800')),  # qty 10, cost 800
        ]
        po = create_purchase_order(
            supplier_id=self.supplier.id,
            expected_date=None,
            notes="Test PO",
            items=items,
            user=self.user
        )
        
        self.assertEqual(PurchaseOrder.objects.count(), 1)
        self.assertEqual(po.total_amount, Decimal('8000')) # 10 * 800
        self.assertEqual(po.items.count(), 1)
        item = po.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.unit_cost, Decimal('800'))

    def test_receive_purchase_items(self):
        """Test receiving items updates stock and status."""
        # 1. Create PO
        items = [(self.product.id, 10, Decimal('800'))]
        po = create_purchase_order(self.supplier.id, None, "Test", items, self.user)
        item = po.items.first()

        # 2. Receive 5 items (Partial)
        received_data = [(item.id, 5)]
        po = receive_purchase_items(po, received_data, self.user)
        
        # Check Item
        item.refresh_from_db()
        self.assertEqual(item.received_quantity, 5)
        
        # Check Product Stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
        
        # Check PO Status
        self.assertEqual(po.status, PURCHASE_ORDERED) # Not fully received yet

        # 3. Receive remaining 5 items (Full)
        received_data = [(item.id, 5)]
        po = receive_purchase_items(po, received_data, self.user)
        
        # Check Item
        item.refresh_from_db()
        self.assertEqual(item.received_quantity, 10)
        
        # Check Product Stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
        
        # Check PO Status
        self.assertEqual(po.status, PURCHASE_RECEIVED)

    def test_receive_more_than_ordered(self):
        """Test validation when receiving more than ordered."""
        items = [(self.product.id, 10, Decimal('800'))]
        po = create_purchase_order(self.supplier.id, None, "Test", items, self.user)
        item = po.items.first()

        received_data = [(item.id, 11)]
        
        with self.assertRaises(ValueError):
            receive_purchase_items(po, received_data, self.user)
