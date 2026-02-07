from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core.models import Product, ProductCategory, UnitOfMeasure

User = get_user_model()

class ProductAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.category = ProductCategory.objects.create(name_en='Test Category', code='CAT001')
        self.unit = UnitOfMeasure.objects.create(name_en='Box', code='BOX')
        self.product = Product.objects.create(
            name='Test Product',
            sku='SKU001',
            category=self.category,
            unit=self.unit,
            base_price=1000,
            stock_quantity=10
        )

    def test_get_products(self):
        """Ensure we can retrieve product list."""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Product')
        self.assertEqual(response.data[0]['category']['name_en'], 'Test Category')

    def test_create_product(self):
        """Ensure we can create a new product."""
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'sku': 'SKU002',
            'base_price': 2000,
            'stock_quantity': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
