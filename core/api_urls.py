from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.api_views import ProductViewSet, ProductCategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', ProductCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
