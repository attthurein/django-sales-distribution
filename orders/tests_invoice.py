from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from customers.models import Customer
from core.models import Product, ProductPriceTier
from master_data.models import CustomerType, ProductCategory, UnitOfMeasure, PaymentMethod, OrderStatus
from orders.models import SalesOrder, Payment, OrderItem
from orders.services import create_order_from_request
from master_data.models import CompanySetting

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class InvoiceAndVoucherTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('setup_master_data')

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'testpass123')
        self.client.force_login(self.user)
        
        # Setup Master Data references
        self.customer_type = CustomerType.objects.get(code='INDIVIDUAL')
        self.payment_method = PaymentMethod.objects.first()
        self.status_pending = OrderStatus.objects.get(code='PENDING')
        
        # Setup Customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='09123456789',
            customer_type=self.customer_type,
            credit_limit=100000
        )
        
        # Setup Product
        cat = ProductCategory.objects.first()
        unit = UnitOfMeasure.objects.first()
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST001',
            category=cat,
            unit=unit,
            base_price=1000,
            stock_quantity=100
        )
        
        # Setup Order
        self.order = SalesOrder.objects.create(
            customer=self.customer,
            order_type='NORMAL',
            total_amount=Decimal('2000'),
            subtotal=Decimal('2000'),
            created_by=self.user,
            status=self.status_pending,
            order_date=timezone.now().date()
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('1000'),
            total_price=Decimal('2000')
        )
        
        # Setup Payment
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('2000'),
            payment_method=self.payment_method,
            payment_date=timezone.now().date(),
            created_by=self.user,
            voucher_number='V-0001'
        )
        
        # Setup Company Setting with Logo
        self.company = CompanySetting.objects.create(
            name="Test Company",
            address="123 Test St",
            phone="099999999",
            footer_text="Test Footer Message"
        )

    def test_invoice_view(self):
        """Test the HTML invoice view."""
        url = reverse('orders:invoice_view', args=[self.order.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/invoice.html')
        self.assertContains(response, 'Test Customer')
        self.assertContains(response, 'Test Product')
        self.assertContains(response, '2,000')  # Check for total formatting
        self.assertContains(response, 'Test Company') # Check company info
        self.assertContains(response, 'Test Footer Message')
        self.assertNotContains(response, 'Thank you for your business!') # Should not show default text if custom footer exists

    def test_invoice_pdf(self):
        """Test the PDF invoice generation."""
        url = reverse('orders:invoice_pdf', args=[self.order.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # PDF content is binary, so we just check status and type

    def test_payment_voucher_view(self):
        """Test the HTML payment voucher view."""
        url = reverse('orders:payment_voucher', args=[self.payment.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/payment_voucher.html')
        self.assertContains(response, 'V-0001')
        self.assertContains(response, 'Amount Received')
        self.assertContains(response, self.payment_method.name_en) # Check payment method display
        self.assertContains(response, 'Test Company')
        self.assertContains(response, 'Test Footer Message')

    def test_payment_voucher_pdf(self):
        """Test the PDF payment voucher generation."""
        url = reverse('orders:payment_voucher_pdf', args=[self.payment.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_invoice_access_permissions(self):
        """Test that invoice requires login."""
        self.client.logout()
        url = reverse('orders:invoice_view', args=[self.order.pk])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200) # Should redirect to login
