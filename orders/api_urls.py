from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.api_views import SalesOrderViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'orders', SalesOrderViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
