"""
Order service tests.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command

from customers.models import Customer
from core.models import Product, ProductPriceTier
from master_data.models import CustomerType, ProductCategory, UnitOfMeasure
from orders.services import create_order_from_request, confirm_order, update_order_items

User = get_user_model()


from orders.models import SalesOrder

class OrderServiceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('setup_master_data')

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'testpass123')
        ct = CustomerType.objects.get(code='INDIVIDUAL')
        self.customer = Customer.objects.create(
            name='Test Customer', phone='09123456789',
            customer_type=ct, credit_limit=100000
        )
        cat = ProductCategory.objects.first()
        unit = UnitOfMeasure.objects.first()
        self.product = Product.objects.create(
            name='Test Product', sku='TEST001',
            category=cat, unit=unit,
            base_price=1000, stock_quantity=100
        )
        ProductPriceTier.objects.create(
            product=self.product, customer_type=ct, price=1000
        )

    def test_create_order(self):
        # Prepare order items as expected by service
        items = [{
            'product': self.product,
            'quantity': 2,
            'unit_price': Decimal('1000'),
            'total_price': Decimal('2000')
        }]
        
        order = create_order_from_request(
            customer=self.customer,
            order_items=items,
            order_type='NORMAL',
            discount_amount=Decimal('0'),
            notes='Test order',
            user=self.user
        )
        
        self.assertEqual(order.orderitem_set.count(), 1)
        self.assertEqual(order.total_amount, Decimal('2000'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 98)

    def test_soft_delete_order(self):
        """Test that soft delete works and objects manager filters correctly."""
        # Create order
        items = [{
            'product': self.product,
            'quantity': 1,
            'unit_price': Decimal('1000'),
            'total_price': Decimal('1000')
        }]
        order = create_order_from_request(
            self.customer, items, 'NORMAL', Decimal('0'), 'Delete me', self.user
        )
        
        # Soft delete
        order.soft_delete()
        
        # Check managers
        self.assertEqual(SalesOrder.objects.count(), 0)
        self.assertEqual(SalesOrder.all_objects.count(), 1)
        self.assertTrue(SalesOrder.all_objects.first().is_deleted)
        
        # Check order number generation ignores deletion (should verify uniqueness logic)
        # get_next_order_number relies on all_objects, so it should see the deleted order
        # and generate next number correctly.
        from orders.services import get_next_order_number
        next_num = get_next_order_number()
        # If previous was ORD-YYYYMMDD-0001, next should be 0002
        # Note: In test, date is today.
        
        # We need to check what the deleted order number was
        last_num_seq = int(order.order_number.split('-')[-1])
        next_num_seq = int(next_num.split('-')[-1])
        self.assertEqual(next_num_seq, last_num_seq + 1)

    def test_edit_confirmed_order_fails(self):
        """Test that confirmed orders cannot be edited."""
        items = [{
            'product': self.product,
            'quantity': 1,
            'unit_price': Decimal('1000'),
            'total_price': Decimal('1000')
        }]
        order = create_order_from_request(
            self.customer, items, 'NORMAL', Decimal('0'), 'Test Edit', self.user
        )
        
        confirm_order(order.id)
        order.refresh_from_db()
        
        new_items = [{
            'product': self.product,
            'quantity': 2,
            'unit_price': Decimal('1000'),
            'total_price': Decimal('2000')
        }]
        
        with self.assertRaises(ValueError) as cm:
            update_order_items(order, new_items, self.user)
        
        self.assertIn("Cannot edit items", str(cm.exception))
