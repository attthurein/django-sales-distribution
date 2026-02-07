from django.urls import path
from . import views

app_name = 'crm'
urlpatterns = [
    path('', views.lead_list, name='lead_list'),
    path('create/', views.lead_create, name='lead_create'),
    path('<int:pk>/', views.lead_detail, name='lead_detail'),
    path('<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('<int:pk>/convert/', views.lead_convert, name='lead_convert'),
    path('<int:lead_id>/contact/', views.contact_log_add, name='contact_log_add'),
    path('<int:lead_id>/sample/', views.sample_give, name='sample_give'),
    path('customer/<int:customer_id>/sample/', views.sample_give_for_customer, name='sample_give_for_customer'),
    path('sample/<int:sample_id>/return/', views.sample_return, name='sample_return'),
    path('sample/<int:sample_id>/not-returned/', views.sample_mark_not_returned, name='sample_mark_not_returned'),
    path('sample/<int:sample_id>/delete/', views.sample_delete, name='sample_delete'),
]
