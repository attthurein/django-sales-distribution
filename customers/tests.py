from django.test import TestCase
from django.core.management import call_command
from customers.models import Customer
from master_data.models import CustomerType, Township, Region

class CustomerModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup master data (CustomerType, etc.)
        call_command('setup_master_data')

    def setUp(self):
        self.customer_type = CustomerType.objects.first()
        # Create a dummy region and township if not exists (though setup_master_data might have)
        self.region = Region.objects.first()
        if not self.region:
            self.region = Region.objects.create(name_en="Yangon", code="YGN")
        
        self.township = Township.objects.first()
        if not self.township:
            self.township = Township.objects.create(name_en="Bahan", code="BHN", region=self.region)

    def test_create_customer(self):
        """Test creating a customer successfully."""
        customer = Customer.objects.create(
            name="Test Customer",
            phone="09123456789",
            customer_type=self.customer_type,
            township=self.township,
            credit_limit=50000
        )
        self.assertEqual(customer.name, "Test Customer")
        self.assertEqual(customer.phone, "09123456789")
        self.assertEqual(customer.credit_limit, 50000)
        self.assertTrue(customer.is_active)
        self.assertIsNone(customer.deleted_at)

    def test_customer_str(self):
        """Test string representation."""
        customer = Customer.objects.create(
            name="Test Customer",
            phone="09123456789",
            customer_type=self.customer_type
        )
        self.assertEqual(str(customer), "Test Customer (09123456789)")

    def test_shop_name_optional(self):
        """Test that shop name is optional."""
        customer = Customer.objects.create(
            name="Individual Customer",
            phone="09987654321",
            customer_type=self.customer_type
        )
        self.assertEqual(customer.shop_name, "")
