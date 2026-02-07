from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customers.api_views import CustomerViewSet, SalespersonViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'salespeople', SalespersonViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
