from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.api_views import (
    ProductViewSet, ProductCategoryViewSet, ProductVariantViewSet,
    ProductPriceTierViewSet, BatchViewSet, StockMovementViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', ProductCategoryViewSet)
router.register(r'variants', ProductVariantViewSet)
router.register(r'price-tiers', ProductPriceTierViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'stock-movements', StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
