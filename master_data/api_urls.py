from django.urls import path, include
from rest_framework.routers import DefaultRouter
from master_data.api_views import (
    CustomerTypeViewSet, RegionViewSet, TownshipViewSet, 
    DeliveryRouteViewSet, PaymentMethodViewSet, OrderStatusViewSet,
    UnitOfMeasureViewSet, SupplierViewSet, PromotionViewSet,
    CurrencyViewSet
)

router = DefaultRouter()
router.register(r'customer-types', CustomerTypeViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'townships', TownshipViewSet)
router.register(r'delivery-routes', DeliveryRouteViewSet)
router.register(r'payment-methods', PaymentMethodViewSet)
router.register(r'order-statuses', OrderStatusViewSet)
router.register(r'uoms', UnitOfMeasureViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'promotions', PromotionViewSet)
router.register(r'currencies', CurrencyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
