from rest_framework import serializers
from .models import Lead, ContactLog, SampleDelivery
from customers.api_views import CustomerSerializer
from core.api_views import ProductSerializer
from master_data.serializers import ContactTypeSerializer, TownshipSerializer

class LeadSerializer(serializers.ModelSerializer):
    township_detail = TownshipSerializer(source='township', read_only=True)
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'shop_name', 'contact_person', 'phone', 'address',
            'township', 'township_detail', 'source', 'status', 'customer', 'customer_detail',
            'assigned_to', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ContactLogSerializer(serializers.ModelSerializer):
    contact_type_detail = ContactTypeSerializer(source='contact_type', read_only=True)
    lead_detail = LeadSerializer(source='lead', read_only=True)
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = ContactLog
        fields = [
            'id', 'lead', 'lead_detail', 'customer', 'customer_detail',
            'contact_type', 'contact_type_detail', 'notes', 'next_follow_up',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_at', 'created_by']

class SampleDeliverySerializer(serializers.ModelSerializer):
    lead_detail = LeadSerializer(source='lead', read_only=True)
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = SampleDelivery
        fields = [
            'id', 'lead', 'lead_detail', 'customer', 'customer_detail',
            'product', 'product_detail', 'quantity', 'status',
            'given_at', 'returned_at', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
