from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('api/product-prices/', views.product_prices_by_customer, name='product_prices_by_customer'),
    path('add/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/edit/', views.order_update, name='order_edit'),
    path('<int:pk>/confirm/', views.order_confirm, name='order_confirm'),
    path('<int:pk>/deliver/', views.order_deliver, name='order_deliver'),
    path('<int:pk>/payment/', views.add_payment, name='order_payment'),
    path('<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('payment/<int:payment_id>/voucher/', views.payment_voucher, name='payment_voucher'),
    path('payment/<int:payment_id>/voucher/pdf/', views.payment_voucher_pdf, name='payment_voucher_pdf'),
    path('<int:pk>/invoice/', views.invoice_view, name='invoice_view'),
    path('<int:pk>/invoice/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
