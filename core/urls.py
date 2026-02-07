from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('movements/', views.stock_movement_list, name='stock_movement_list'),
    path('low-stock/', views.low_stock_list, name='low_stock_list'),
    path(
        'batches/<int:product_id>/',
        views.batches_for_product,
        name='batches_for_product',
    ),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/adjust/', views.stock_adjust, name='stock_adjust'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
]
