from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'leads', api_views.LeadViewSet)
router.register(r'contact-logs', api_views.ContactLogViewSet)
router.register(r'sample-deliveries', api_views.SampleDeliveryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
