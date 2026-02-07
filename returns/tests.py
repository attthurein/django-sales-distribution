from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from customers.models import Customer
from core.models import Product, ProductPriceTier
from master_data.models import CustomerType, ProductCategory, UnitOfMeasure, ReturnType, ReturnReason
from orders.models import SalesOrder, OrderItem
from master_data.constants import ORDER_DELIVERED, ORDER_PAID
from master_data.models import OrderStatus
from returns.services import create_return_request

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ReturnRestrictionTests(TestCase):
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
        
        # Create a delivered order
        self.delivered_status = OrderStatus.objects.get(code=ORDER_DELIVERED)
        self.order = SalesOrder.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            status=self.delivered_status,
            delivery_date=timezone.now().date(),
            total_amount=2000,
            created_by=self.user
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=1000,
            total_price=2000
        )
        
        self.return_type = ReturnType.objects.first()
        self.return_reason = ReturnReason.objects.first()

    def test_prevent_multiple_return_requests(self):
        # Create first return request
        items_with_reasons = [{
            'order_item_id': self.order_item.id,
            'quantity': 1,
            'reason_id': self.return_reason.id,
            'condition_notes': 'Defective'
        }]
        
        create_return_request(
            self.order,
            items_with_reasons,
            self.return_type,
            'First return'
        )
        
        # Try to create second return request
        items_with_reasons_2 = [{
            'order_item_id': self.order_item.id,
            'quantity': 1,
            'reason_id': self.return_reason.id,
            'condition_notes': 'Defective again'
        }]
        
        # We expect this to FAIL after our changes.
        # But for now, we want to confirm it SUCCEEDS (current behavior) or we can just write the test expecting failure and see it fail.
        # I will write it expecting failure (ValueError), so the test will FAIL now, and PASS after I fix it.
        
        with self.assertRaises(ValueError) as cm:
            create_return_request(
                self.order,
                items_with_reasons_2,
                self.return_type,
                'Second return'
            )
        self.assertIn("This order already has a return request", str(cm.exception))

    def test_return_create_view_filters_existing_returns(self):
        # Create a return request first
        items_with_reasons = [{
            'order_item_id': self.order_item.id,
            'quantity': 1,
            'reason_id': self.return_reason.id,
            'condition_notes': 'Defective'
        }]
        create_return_request(
            self.order,
            items_with_reasons,
            self.return_type,
            'First return'
        )
        
        # Login
        self.client.force_login(self.user)
        
        # We need permission to access the view
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename='add_returnrequest')
        self.user.user_permissions.add(permission)
        
        # Access return create page
        from django.urls import reverse
        response = self.client.get(reverse('returns:return_create'))
        
        self.assertEqual(response.status_code, 200)
        
        # The order should NOT be in the 'orders' context because it already has a return
        orders_in_context = response.context['orders']
        self.assertNotIn(self.order, orders_in_context)
        
        # Create another order without return
        order2 = SalesOrder.objects.create(
            customer=self.customer,
            order_number='ORD-002',
            status=self.delivered_status,
            delivery_date=timezone.now().date(),
            total_amount=2000,
            created_by=self.user
        )
        
        response = self.client.get(reverse('returns:return_create'))
        orders_in_context = response.context['orders']
        self.assertIn(order2, orders_in_context)
