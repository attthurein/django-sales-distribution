from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'expense-categories', api_views.ExpenseCategoryViewSet)
router.register(r'expenses', api_views.ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
