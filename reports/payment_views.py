"""
Payment report views.
"""
import csv
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from datetime import datetime
from orders.models import Payment, SalesOrder
from customers.models import Customer
from master_data.models import PaymentMethod
from master_data.constants import PURCHASE_RECEIVED, ORDER_CANCELLED
from openpyxl import Workbook
from reports.utils import _export_pdf, _export_excel, _export_csv


@login_required
@permission_required('orders.view_payment', raise_exception=True)
def payment_report(request):
    """Daily payment report with filters"""
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Base queryset
    payments = Payment.objects.select_related(
        'order', 'order__customer', 'payment_method', 'created_by'
    ).all()
    
    # Apply filters
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    if payment_method:
        payments = payments.filter(payment_method_id=payment_method)
    
    # Calculate summary
    summary = payments.aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    # Group by payment method
    by_method = payments.values(
        'payment_method__name_en'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Group by date
    by_date = payments.values('payment_date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-payment_date')
    
    context = {
        'title': 'Payment Report',
        'payments': payments.order_by('-payment_date', '-created_at'),
        'summary': summary,
        'by_method': by_method,
        'by_date': by_date,
        'date_from': date_from,
        'date_to': date_to,
        'payment_method': payment_method,
        'payment_methods': PaymentMethod.objects.filter(is_active=True),
    }
    return render(request, 'reports/payment_report.html', context)


@login_required
@permission_required('orders.view_payment', raise_exception=True)
def export_payments(request):
    """Export payments to Excel, PDF or CSV."""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    payments = Payment.objects.select_related(
        'order', 'order__customer', 'payment_method', 'created_by'
    ).all()
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    if payment_method:
        payments = payments.filter(payment_method_id=payment_method)
    
    headers = [
        'Voucher Number', 'Date', 'Order Number', 'Customer', 
        'Amount', 'Payment Method', 'Reference', 'Recorded By'
    ]
    rows = []
    for payment in payments.order_by('-payment_date'):
        rows.append([
            payment.voucher_number or '',
            payment.payment_date.strftime('%Y-%m-%d'),
            payment.order.order_number,
            payment.order.customer.name,
            str(payment.amount),
            payment.payment_method.name_en if payment.payment_method else '',
            payment.reference_number or '',
            payment.created_by.username if payment.created_by else ''
        ])
    
    fmt = request.GET.get('format', 'xlsx')
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payments_{datetime.now().strftime("%Y%m%d")}.pdf"'
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, rows, headers, title='Payments Report', orientation=orientation)

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payments_{datetime.now().strftime("%Y%m%d")}.csv"'
        return _export_csv(response, rows, headers)

    # Excel (default)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="payments_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    return _export_excel(response, rows, headers, 'Payments') or response


@login_required
@permission_required('orders.view_payment', raise_exception=True)
def outstanding_payments_report(request):
    """Outstanding payments - orders/customers with balance due."""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    customer_id = request.GET.get('customer_id', '')

    # Orders with balance due (total_amount > paid_amount)
    # Exclude Cancelled orders
    from master_data.constants import ORDER_CANCELLED
    
    orders_qs = SalesOrder.objects.filter(
        total_amount__gt=F('paid_amount')
    ).exclude(
        status__code=ORDER_CANCELLED
    ).select_related('customer', 'status').order_by('-created_at')

    if date_from:
        orders_qs = orders_qs.filter(order_date__gte=date_from)
    if date_to:
        orders_qs = orders_qs.filter(order_date__lte=date_to)
    if customer_id:
        orders_qs = orders_qs.filter(customer_id=customer_id)

    outstanding_list = []
    for order in orders_qs:
        balance_due = order.total_amount - order.paid_amount
        outstanding_list.append({
            'order': order,
            'order_number': order.order_number,
            'customer': order.customer,
            'order_date': order.order_date,
            'total_amount': order.total_amount,
            'paid_amount': order.paid_amount,
            'balance_due': balance_due,
            'status': order.status,
        })

    # Summary by customer
    customer_totals_qs = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        total_amount__gt=F('paid_amount')
    ).exclude(
        status__code=ORDER_CANCELLED
    )
    if date_from:
        customer_totals_qs = customer_totals_qs.filter(order_date__gte=date_from)
    if date_to:
        customer_totals_qs = customer_totals_qs.filter(order_date__lte=date_to)
    if customer_id:
        customer_totals_qs = customer_totals_qs.filter(customer_id=customer_id)
    customer_totals = customer_totals_qs.values(
        'customer__id', 'customer__name', 'customer__phone'
    ).annotate(
        total_due=Sum(F('total_amount') - F('paid_amount')),
        order_count=Count('id')
    ).order_by('-total_due')

    context = {
        'title': 'Outstanding Payments',
        'outstanding_list': outstanding_list,
        'customer_totals': customer_totals,
        'date_from': date_from,
        'date_to': date_to,
        'customer_id': customer_id,
        'customers': Customer.objects.filter(deleted_at__isnull=True, is_active=True).order_by('name'),
    }
    return render(request, 'reports/outstanding_payments.html', context)


@login_required
@permission_required('orders.view_payment', raise_exception=True)
def export_outstanding(request):
    """Export outstanding payments to CSV/Excel/PDF."""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    customer_id = request.GET.get('customer_id', '')

    orders_qs = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        total_amount__gt=F('paid_amount')
    ).exclude(
        status__code=ORDER_CANCELLED
    ).select_related('customer', 'status').order_by('-order_date')

    if date_from:
        orders_qs = orders_qs.filter(order_date__gte=date_from)
    if date_to:
        orders_qs = orders_qs.filter(order_date__lte=date_to)
    if customer_id:
        orders_qs = orders_qs.filter(customer_id=customer_id)

    headers = ['Order #', 'Customer', 'Order Date', 'Total', 'Paid', 'Balance Due', 'Status']
    rows = []
    for o in orders_qs:
        balance = o.total_amount - o.paid_amount
        rows.append([
            o.order_number,
            o.customer.name,
            o.order_date.strftime('%Y-%m-%d'),
            str(o.total_amount),
            str(o.paid_amount),
            str(balance),
            o.status.name_en if o.status else '',
        ])

    fmt = request.GET.get('format', 'csv')
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="outstanding_{datetime.now().strftime("%Y%m%d")}.pdf"'
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, rows, headers, title='Outstanding Payments', orientation=orientation)

    if fmt == 'xlsx':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="outstanding_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        return _export_excel(response, rows, headers, 'Outstanding') or response

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="outstanding_{datetime.now().strftime("%Y%m%d")}.csv"'
    return _export_csv(response, rows, headers)


@login_required
@permission_required('orders.view_payment', raise_exception=True)
def payment_by_customer_report(request):
    """Payment summary by customer."""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    payments_qs = Payment.objects.select_related(
        'order', 'order__customer', 'payment_method'
    ).all()

    if date_from:
        payments_qs = payments_qs.filter(payment_date__gte=date_from)
    if date_to:
        payments_qs = payments_qs.filter(payment_date__lte=date_to)

    by_customer = payments_qs.values(
        'order__customer__id', 'order__customer__name', 'order__customer__phone'
    ).annotate(
        total_paid=Sum('amount'),
        payment_count=Count('id')
    ).order_by('-total_paid')

    fmt = request.GET.get('format')
    if fmt in ['csv', 'xlsx', 'pdf']:
        headers = ['Customer', 'Phone', 'Count', 'Total Paid']
        rows = []
        for row in by_customer:
            rows.append([
                row['order__customer__name'],
                row['order__customer__phone'] or '-',
                str(row['payment_count']),
                str(row['total_paid'])
            ])
            
        if fmt == 'pdf':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payment_by_customer_{datetime.now().strftime("%Y%m%d")}.pdf"'
            orientation = request.GET.get('orientation', 'portrait')
            return _export_pdf(response, rows, headers, title='Payment by Customer', orientation=orientation)
            
        if fmt == 'xlsx':
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="payment_by_customer_{datetime.now().strftime("%Y%m%d")}.xlsx"'
            result = _export_excel(response, rows, headers, 'PaymentByCustomer')
            if result:
                return result
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payment_by_customer_{datetime.now().strftime("%Y%m%d")}.csv"'
        return _export_csv(response, rows, headers)

    context = {
        'title': 'Payment by Customer',
        'by_customer': by_customer,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/payment_by_customer.html', context)
