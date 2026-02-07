from rest_framework import serializers
from core.models import Product, ProductCategory, ProductVariant, ProductPriceTier, Batch, StockMovement
from master_data.models import UnitOfMeasure, CustomerType
from master_data.serializers import CustomerTypeSerializer

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'code', 'name_en', 'name_my']

class UnitOfMeasureSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name_en', 'name_my']

class ProductSerializer(serializers.ModelSerializer):
    category_detail = ProductCategorySerializer(source='category', read_only=True)
    unit_detail = UnitOfMeasureSimpleSerializer(source='unit', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_detail', 'unit', 'unit_detail',
            'base_price', 'stock_quantity', 'is_low_stock',
            'expiry_date', 'is_active', 'created_at', 'updated_at'
        ]

class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'product_name', 'name', 'sku_suffix',
            'price_adjustment', 'stock_quantity', 'is_active',
            'created_at', 'updated_at'
        ]

class ProductPriceTierSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    customer_type_detail = CustomerTypeSerializer(source='customer_type', read_only=True)

    class Meta:
        model = ProductPriceTier
        fields = [
            'id', 'product', 'product_name', 'customer_type', 'customer_type_detail', 'price'
        ]

class BatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'product', 'product_name', 'batch_number', 'quantity',
            'expiry_date', 'received_at', 'notes', 'created_at'
        ]

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'batch', 'batch_number',
            'movement_type', 'quantity', 'reference_type', 'reference_id',
            'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_at', 'created_by']

class StockAdjustmentSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
