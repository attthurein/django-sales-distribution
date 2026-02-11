"""
Master Data URL configuration.
"""
from django.urls import path
from . import views

app_name = 'master_data'

urlpatterns = [
    path('company-setting/', views.company_setting, name='company_setting'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
]
