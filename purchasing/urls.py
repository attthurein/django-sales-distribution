from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('', views.purchase_order_list, name='purchase_order_list'),
    path('create/', views.purchase_order_create, name='purchase_order_create'),
    path('<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
]
