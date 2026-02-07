from rest_framework import viewsets, permissions
from master_data.models import (
    CustomerType, Region, Township, DeliveryRoute, 
    PaymentMethod, OrderStatus, UnitOfMeasure,
    Supplier, Promotion, Currency
)
from master_data.serializers import (
    CustomerTypeSerializer, RegionSerializer, TownshipSerializer, 
    DeliveryRouteSerializer, PaymentMethodSerializer, OrderStatusSerializer,
    UnitOfMeasureSerializer, SupplierSerializer, PromotionSerializer,
    CurrencySerializer
)

class BaseMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """Base ViewSet for read-only master data"""
    permission_classes = [permissions.IsAuthenticated]

class CustomerTypeViewSet(BaseMasterViewSet):
    queryset = CustomerType.objects.filter(is_active=True).order_by('sort_order')
    serializer_class = CustomerTypeSerializer

class RegionViewSet(BaseMasterViewSet):
    queryset = Region.objects.filter(is_active=True).order_by('code')
    serializer_class = RegionSerializer

class TownshipViewSet(BaseMasterViewSet):
    queryset = Township.objects.filter(is_active=True).order_by('region__code', 'name_en')
    serializer_class = TownshipSerializer
    filterset_fields = ['region', 'delivery_route']

class DeliveryRouteViewSet(BaseMasterViewSet):
    queryset = DeliveryRoute.objects.filter(is_active=True).order_by('code')
    serializer_class = DeliveryRouteSerializer

class PaymentMethodViewSet(BaseMasterViewSet):
    queryset = PaymentMethod.objects.filter(is_active=True).order_by('code')
    serializer_class = PaymentMethodSerializer

class OrderStatusViewSet(BaseMasterViewSet):
    queryset = OrderStatus.objects.filter(is_active=True).order_by('sort_order')
    serializer_class = OrderStatusSerializer

class UnitOfMeasureViewSet(BaseMasterViewSet):
    queryset = UnitOfMeasure.objects.filter(is_active=True).order_by('code')
    serializer_class = UnitOfMeasureSerializer

class SupplierViewSet(BaseMasterViewSet):
    queryset = Supplier.objects.filter(is_active=True).order_by('name_en')
    serializer_class = SupplierSerializer

class PromotionViewSet(BaseMasterViewSet):
    queryset = Promotion.objects.filter(is_active=True).order_by('-end_date')
    serializer_class = PromotionSerializer

class CurrencyViewSet(BaseMasterViewSet):
    queryset = Currency.objects.filter(is_active=True).order_by('sort_order')
    serializer_class = CurrencySerializer
