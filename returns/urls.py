from django.urls import path
from . import views

app_name = 'returns'

urlpatterns = [
    path('', views.return_list, name='return_list'),
    path('create/', views.return_create, name='return_create'),
    path('create/items/<int:order_id>/', views.return_create_items, name='return_create_items'),
    path('<int:pk>/', views.return_detail, name='return_detail'),
    path('<int:pk>/delete/', views.return_delete, name='return_delete'),
    path('<int:pk>/approve/', views.approve_return, name='approve_return'),
    path('<int:pk>/reject/', views.reject_return, name='reject_return'),
    path('<int:pk>/create-replacement/', views.create_replacement_order, name='create_replacement_order'),
    path('api/get-order-items/', views.get_order_items, name='get_order_items'),
]
