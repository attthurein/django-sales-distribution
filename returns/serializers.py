from rest_framework import serializers
from .models import ReturnRequest, ReturnItem, ReturnProcessing
from orders.api_views import SalesOrderSerializer
from orders.serializers import OrderItemSerializer
from core.api_views import ProductSerializer
from master_data.serializers import ReturnReasonSerializer, ReturnRequestStatusSerializer, ReturnTypeSerializer

class ReturnItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    reason_detail = ReturnReasonSerializer(source='reason', read_only=True)
    order_item_detail = OrderItemSerializer(source='order_item', read_only=True)

    class Meta:
        model = ReturnItem
        fields = [
            'id', 'return_request', 'order_item', 'order_item_detail',
            'product', 'product_detail', 'quantity',
            'reason', 'reason_detail', 'return_to_stock', 'condition_notes'
        ]

class ReturnProcessingSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)

    class Meta:
        model = ReturnProcessing
        fields = [
            'id', 'return_request', 'action', 'notes',
            'processed_by', 'processed_by_name', 'processed_at'
        ]
        read_only_fields = ['processed_at', 'processed_by']

class ReturnRequestSerializer(serializers.ModelSerializer):
    status_detail = ReturnRequestStatusSerializer(source='status', read_only=True)
    return_type_detail = ReturnTypeSerializer(source='return_type', read_only=True)
    order_detail = SalesOrderSerializer(source='order', read_only=True)
    items = ReturnItemSerializer(many=True, read_only=True)
    processing_log = ReturnProcessingSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'order', 'order_detail', 'return_number',
            'status', 'status_detail', 'return_type', 'return_type_detail',
            'replacement_order', 'total_amount', 'notes',
            'created_at', 'updated_at', 'items', 'processing_log'
        ]
        read_only_fields = ['return_number', 'total_amount', 'created_at', 'updated_at']

class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True)

    class Meta:
        model = ReturnRequest
        fields = [
            'order', 'status', 'return_type', 'notes', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # return_number generation is handled in model save() or signal? 
        # Checking model... model doesn't seem to have auto-gen in save() from previous read.
        # Assuming for now it needs to be provided or handled. 
        # Wait, usually unique numbers are auto-generated.
        # Let's generate a simple one if not present, or assume the view handles it.
        # For now, I'll generate a basic one if not provided, but usually it's better in the model.
        # I'll let the view or signal handle it if it exists. 
        # But looking at models.py again, return_number is mandatory.
        
        import uuid
        if 'return_number' not in validated_data:
            validated_data['return_number'] = f"RET-{uuid.uuid4().hex[:8].upper()}"

        return_request = ReturnRequest.objects.create(**validated_data)
        
        for item_data in items_data:
            ReturnItem.objects.create(return_request=return_request, **item_data)
            
        return return_request
