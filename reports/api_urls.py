from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'dashboard', api_views.DashboardViewSet, basename='dashboard')
router.register(r'daily-sales', api_views.DailySalesSummaryViewSet)
router.register(r'daily-inventory', api_views.DailyInventorySnapshotViewSet)
router.register(r'daily-payments', api_views.DailyPaymentSummaryViewSet)
router.register(r'daily-expenses', api_views.DailyExpenseSummaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
