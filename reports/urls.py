from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.report_index, name='report_index'),
    path('sales/', views.sales_report, name='sales_report'),
    path('returns/', views.return_report, name='return_report'),
    path('purchase-vs-sales/', views.purchase_vs_sales_report, name='purchase_vs_sales'),
    path('profit-analysis/', views.profit_analysis_report, name='profit_analysis'),
    path('export/orders/', views.export_orders, name='export_orders'),
    path('export/returns/', views.export_returns, name='export_returns'),
    path('export/inventory/', views.export_inventory, name='export_inventory'),
    path('payments/', views.payment_report, name='payment_report'),
    path('export/payments/', views.export_payments, name='export_payments'),
    path('outstanding/', views.outstanding_payments_report, name='outstanding_payments'),
    path('export/outstanding/', views.export_outstanding, name='export_outstanding'),
    path('payment-by-customer/', views.payment_by_customer_report, name='payment_by_customer'),
    path('audit-log/', views.audit_log_report, name='audit_log_report'),
    path('export/audit-log/', views.export_audit_log, name='export_audit_log'),
]
