from rest_framework import serializers
from .models import PurchaseOrder, PurchaseItem
from core.api_views import ProductSerializer
from master_data.serializers import SupplierSerializer

class PurchaseItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = [
            'id', 'purchase_order', 'product', 'product_detail',
            'quantity', 'unit_cost', 'total_cost', 'received_quantity'
        ]
        read_only_fields = ['total_cost']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_detail = SupplierSerializer(source='supplier', read_only=True)
    items = PurchaseItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'supplier', 'supplier_detail', 'order_date', 'expected_date',
            'status', 'reference_number', 'notes', 'total_amount',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = ['total_amount', 'created_at', 'updated_at', 'created_by']

class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'expected_date', 'status', 'reference_number', 'notes', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        
        total_amount = 0
        for item_data in items_data:
            # total_cost is calculated in model save()
            item = PurchaseItem.objects.create(purchase_order=purchase_order, **item_data)
            total_amount += item.total_cost
            
        purchase_order.total_amount = total_amount
        purchase_order.save()
        return purchase_order
