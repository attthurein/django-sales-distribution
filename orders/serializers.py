from rest_framework import serializers
from orders.models import SalesOrder, OrderItem, Payment
from core.serializers import ProductSerializer
from customers.serializers import CustomerSerializer
from master_data.models import OrderStatus, PaymentMethod

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_detail', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['total_price']

class OrderStatusSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'code', 'name_en', 'name_my']

class PaymentMethodSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'code', 'name_en', 'name_my']

class PaymentSerializer(serializers.ModelSerializer):
    payment_method_detail = PaymentMethodSimpleSerializer(source='payment_method', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'voucher_number', 'payment_date',
            'amount', 'payment_method', 'payment_method_detail',
            'reference_number', 'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['voucher_number', 'created_at', 'created_by']

class SalesOrderSerializer(serializers.ModelSerializer):
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    status_detail = OrderStatusSimpleSerializer(source='status', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'order_date', 'delivery_date',
            'customer', 'customer_detail',
            'subtotal', 'discount_amount', 'delivery_fee', 'total_amount',
            'paid_amount', 'applied_promotion', 'order_type',
            'status', 'status_detail', 'notes',
            'items', 'payments', 'created_at'
        ]
        read_only_fields = ['order_number', 'subtotal', 'discount_amount', 'total_amount', 'created_by']

class CreateOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders with items
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = SalesOrder
        fields = [
            'customer', 'order_date', 'delivery_date', 
            'order_type', 'notes', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Auto-generate order number (simplified logic for API)
        import uuid
        from django.utils import timezone
        
        # In real app, reuse the generation logic from services or views
        prefix = timezone.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:6].upper()
        validated_data['order_number'] = f"SO-{prefix}-{unique_id}"
        
        order = SalesOrder.objects.create(**validated_data)
        
        # Create items
        total = 0
        for item_data in items_data:
            # item_data should contain 'product_id' and 'quantity'
            from core.models import Product
            product_id = item_data.get('product') or item_data.get('product_id')
            qty = item_data.get('quantity', 1)
            
            product = Product.objects.get(pk=product_id)
            unit_price = product.base_price # Use base_price from product
            total_price = unit_price * qty
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price
            )
            total += total_price
            
        # Update order totals (save() method handles logic but we need to trigger it properly)
        order.subtotal = total
        order.save() # This triggers calculate delivery fee and promotion
        return order
