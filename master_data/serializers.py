from rest_framework import serializers
from master_data.models import (
    CustomerType, Region, Township, DeliveryRoute, 
    PaymentMethod, OrderStatus, UnitOfMeasure,
    Supplier, Promotion, Currency,
    ContactType, ReturnReason, ReturnType, ReturnRequestStatus,
    Country
)

class CustomerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerType
        fields = ['id', 'code', 'name_en', 'name_my', 'sort_order']

class ContactTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactType
        fields = ['id', 'code', 'name_en', 'name_my', 'sort_order']

class ReturnReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnReason
        fields = ['id', 'code', 'name_en', 'name_my', 'requires_notes']

class ReturnTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnType
        fields = ['id', 'code', 'name_en', 'name_my']

class ReturnRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequestStatus
        fields = ['id', 'code', 'name_en', 'name_my', 'sort_order']

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'code', 'name_en', 'name_my', 'sort_order']

class RegionSerializer(serializers.ModelSerializer):
    country_detail = CountrySerializer(source='country', read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'code', 'name_en', 'name_my', 'country', 'country_detail']

class DeliveryRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRoute
        fields = ['id', 'code', 'name_en', 'name_my']

class TownshipSerializer(serializers.ModelSerializer):
    region_detail = RegionSerializer(source='region', read_only=True)
    delivery_route_detail = DeliveryRouteSerializer(source='delivery_route', read_only=True)
    
    class Meta:
        model = Township
        fields = ['id', 'code', 'name_en', 'name_my', 'region', 'region_detail', 'delivery_route', 'delivery_route_detail', 'delivery_fee']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'code', 'name_en', 'name_my']

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'code', 'name_en', 'name_my', 'sort_order']

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name_en', 'name_my']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'code', 'name_en', 'name_my', 'address', 'phone', 'email', 'contact_person']

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['id', 'code', 'name_en', 'name_my', 'start_date', 'end_date', 'discount_percent', 'description']

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name_en', 'name_my', 'symbol', 'sort_order']
