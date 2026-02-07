from rest_framework import serializers
from customers.models import Customer, Salesperson
from master_data.models import Township, CustomerType

class TownshipSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Township
        fields = ['id', 'name_en', 'name_my', 'delivery_fee']

class CustomerTypeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerType
        fields = ['id', 'code', 'name_en', 'name_my']

class SalespersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salesperson
        fields = ['id', 'name', 'phone']

class CustomerSerializer(serializers.ModelSerializer):
    township_detail = TownshipSimpleSerializer(source='township', read_only=True)
    customer_type_detail = CustomerTypeSimpleSerializer(source='customer_type', read_only=True)
    salesperson_detail = SalespersonSerializer(source='salesperson', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'shop_name', 'contact_person', 'phone',
            'customer_type', 'customer_type_detail',
            'township', 'township_detail',
            'salesperson', 'salesperson_detail',
            'street_address', 'credit_limit', 'payment_terms_days',
            'is_active', 'created_at'
        ]
