from rest_framework import serializers
from core.models import Product, ProductCategory, UnitOfMeasure

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'code', 'name_en', 'name_my']

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name_en', 'name_my']

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    unit = UnitOfMeasureSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'unit',
            'base_price', 'stock_quantity', 'is_low_stock',
            'expiry_date', 'is_active', 'created_at', 'updated_at'
        ]
