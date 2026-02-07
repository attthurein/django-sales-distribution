from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'purchase-orders', api_views.PurchaseOrderViewSet)
router.register(r'purchase-items', api_views.PurchaseItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
