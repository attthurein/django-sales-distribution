from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'audit-logs', api_views.AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
