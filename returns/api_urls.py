from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'return-requests', api_views.ReturnRequestViewSet)
router.register(r'return-items', api_views.ReturnItemViewSet)
router.register(r'return-processing', api_views.ReturnProcessingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
