"""
Reports views.
"""
from decimal import Decimal
from io import BytesIO
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta, datetime

from orders.models import SalesOrder, OrderItem, Payment
from core.models import Product, StockMovement
from returns.models import ReturnItem, ReturnRequest
from master_data.models import OrderStatus, ReturnReason
from master_data.constants import PURCHASE_RECEIVED
from common.models import AuditLog
from accounting.models import Expense
from customers.models import Customer
from common.constants import (
    LIMIT_EXPORT_ROWS,
    LIMIT_AUDIT_LOG_DISPLAY,
    LIMIT_AUDIT_LOG_EXPORT,
)
from django.db.models.functions import TruncDate

# Map technical model names to human-readable module names for audit log display
MODULE_DISPLAY_NAMES = {
    'customers.customer': 'Customer',
    'customers.salesperson': 'Salesperson',
    'core.product': 'Product',
    'core.productvariant': 'Product Variant',
    'core.batch': 'Batch',
    'orders.salesorder': 'Sales Order',
    'orders.orderitem': 'Order Item',
    'orders.payment': 'Payment',
    'returns.returnrequest': 'Return Request',
    'returns.returnitem': 'Return Item',
    'crm.lead': 'Lead',
    'crm.contactlog': 'Contact Log',
    'crm.sampledelivery': 'Sample Delivery',
    'purchasing.purchaseorder': 'Purchase Order',
    'purchasing.purchaseitem': 'Purchase Item',
    'accounting.expense': 'Expense',
    'accounting.expensecategory': 'Expense Category',
}


def _get_module_display_name(model_name):
    """Return human-readable module name for audit log."""
    return MODULE_DISPLAY_NAMES.get(model_name, model_name)


def _parse_audit_log_date_range(start_date, end_date, default_days=7):
    """Parse start/end date strings. Returns (start, end) as date objects."""
    from datetime import datetime
    today = timezone.now().date()
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start = today - timedelta(days=default_days)
        end = today
    return start, end


def _get_audit_log_queryset(start, end, action_filter, model_filter):
    """Base AuditLog queryset with date and optional filters."""
    qs = AuditLog.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end
    ).select_related('user').order_by('-created_at')
    if action_filter:
        qs = qs.filter(action=action_filter)
    if model_filter:
        qs = qs.filter(model_name=model_filter)
    return qs


def _get_audit_log_grouped(group_by, start, end, action_filter, model_filter):
    """Build grouped summary for audit log (by date, action, or model)."""
    if not group_by:
        return None
    base = AuditLog.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end
    )
    if group_by == 'date':
        if action_filter:
            base = base.filter(action=action_filter)
        if model_filter:
            base = base.filter(model_name=model_filter)
        return base.annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('-day')
    if group_by == 'action':
        if model_filter:
            base = base.filter(model_name=model_filter)
        return base.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
    if group_by == 'model':
        if action_filter:
            base = base.filter(action=action_filter)
        result = list(
            base.values('model_name').annotate(count=Count('id')).order_by('-count')
        )
        for row in result:
            row['module_display_name'] = _get_module_display_name(row['model_name'])
        return result
    return None


from .models import DailySalesSummary, DailyInventorySnapshot, DailyPaymentSummary, DailyExpenseSummary

@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def dashboard(request):
    """Executive Dashboard showing daily summaries."""
    from datetime import timedelta
    
    # Get last 7 days including today
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    # Prepare data structure
    data = {
        'labels': [d.strftime('%Y-%m-%d') for d in dates],
        'revenue': [],
        'orders': [],
        'payments': [],
        'expenses': []
    }
    
    # Fetch summaries
    # We could optimize this with __in=dates, but list comprehension ensures correct order/zero-filling
    sales_map = {
        s.date: s for s in DailySalesSummary.objects.filter(date__in=dates)
    }
    payment_map = {
        p.date: p for p in DailyPaymentSummary.objects.filter(date__in=dates)
    }
    expense_map = {
        e.date: e for e in DailyExpenseSummary.objects.filter(date__in=dates)
    }
    
    for d in dates:
        s = sales_map.get(d)
        p = payment_map.get(d)
        e = expense_map.get(d)
        
        data['revenue'].append(float(s.total_revenue) if s else 0)
        data['orders'].append(s.total_orders if s else 0)
        data['payments'].append(float(p.total_collected) if p else 0)
        data['expenses'].append(float(e.total_expense) if e else 0)

    # Key Metrics (Today) - LIVE QUERY for Real-time Accuracy
    # We do NOT rely on summary tables for today because the command might not have run yet.
    today_sales_agg = SalesOrder.objects.filter(
        created_at__date=today,
        deleted_at__isnull=True
    ).aggregate(
        rev=Sum('total_amount'),
        cnt=Count('id')
    )
    
    today_payment_agg = Payment.objects.filter(
        payment_date=today,
        deleted_at__isnull=True
    ).aggregate(
        total=Sum('amount')
    )
    
    today_expense_agg = Expense.objects.filter(
        date=today,
        deleted_at__isnull=True
    ).aggregate(
        total=Sum('amount')
    )

    today_summary = {
        'revenue': today_sales_agg['rev'] or 0,
        'orders': today_sales_agg['cnt'] or 0,
        'payments': today_payment_agg['total'] or 0,
        'expenses': today_expense_agg['total'] or 0,
    }
    
    # Update chart data for today (last point) with live data if summary is missing or stale
    # dates[-1] is Today because range(6, -1, -1) produces [Today-6, ..., Today]
    if dates[-1] == today:
        data['revenue'][-1] = float(today_summary['revenue'])
        data['orders'][-1] = today_summary['orders']
        data['payments'][-1] = float(today_summary['payments'])
        data['expenses'][-1] = float(today_summary['expenses'])

    return render(request, 'reports/dashboard.html', {
        'chart_data': data,
        'today_summary': today_summary
    })

# Import payment report functions
from .payment_views import (
    payment_report, export_payments,
    outstanding_payments_report, export_outstanding,
    payment_by_customer_report,
)


from .utils import _export_csv, _export_excel, _export_pdf

@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def export_orders(request):
    """Export orders to CSV or Excel or PDF."""
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status_id = request.GET.get('status', '')
    customer_id = request.GET.get('customer', '')
    period = request.GET.get('period', 'month')
    
    today = timezone.now().date()
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end = today
        if period == 'day':
            start = today
        elif period == 'week':
            start = today - timedelta(days=7)
        else:
            start = today - timedelta(days=30)
            
    orders = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        total_amount__gt=0,
        created_at__date__gte=start,
        created_at__date__lte=end
    ).select_related('customer', 'status').prefetch_related(
        'orderitem_set__product'
    ).order_by('-created_at')

    if status_id:
        orders = orders.filter(status_id=status_id)
    if customer_id:
        orders = orders.filter(customer_id=customer_id)

    # Apply limit only if not exporting all (optional, but good for performance)
    # But for export, user usually wants all matching records. 
    # Let's limit to reasonable amount if no specific filters to avoid memory crash, 
    # but 1000 (LIMIT_EXPORT_ROWS) is usually fine.
    orders = orders[:LIMIT_EXPORT_ROWS]

    fmt = request.GET.get('format', 'csv')
    headers = ['Order #', 'Customer', 'Status', 'Total', 'Date', 'Items']
    rows = []
    for o in orders:
        item_summary = ', '.join(f"{i.product.name} x{i.quantity}" for i in o.orderitem_set.all()[:5])
        if o.orderitem_set.count() > 5:
            item_summary += '...'
        rows.append([
            o.order_number,
            o.customer.name,
            o.status.name_en if o.status else '',
            str(o.total_amount),
            o.created_at.strftime('%Y-%m-%d'),
            item_summary,
        ])
    
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="orders_export.pdf"'
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, rows, headers, title=f"Sales Report ({start} to {end})", orientation=orientation)

    if fmt == 'xlsx':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="orders_export.xlsx"'
        result = _export_excel(response, rows, headers, 'Orders')
        if result:
            return result
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    return _export_csv(response, rows, headers)


@login_required
@permission_required('returns.view_returnrequest', raise_exception=True)
def export_returns(request):
    """Export returns to CSV or Excel or PDF."""
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    reason_id = request.GET.get('reason', '')
    product_id = request.GET.get('product', '')
    
    returns = ReturnRequest.objects.filter(
        deleted_at__isnull=True
    ).select_related(
        'order', 'status', 'return_type'
    ).order_by('-created_at')
    
    if start_date:
        returns = returns.filter(created_at__date__gte=start_date)
    if end_date:
        returns = returns.filter(created_at__date__lte=end_date)
    if reason_id:
        returns = returns.filter(returnitem__reason_id=reason_id).distinct()
    if product_id:
        returns = returns.filter(returnitem__product_id=product_id).distinct()
        
    returns = returns[:LIMIT_EXPORT_ROWS]

    fmt = request.GET.get('format', 'csv')
    headers = ['Return #', 'Order #', 'Status', 'Type', 'Amount', 'Date']
    rows = [[r.return_number, r.order.order_number, r.status.name_en if r.status else '',
             r.return_type.name_en if r.return_type else '', str(r.total_amount),
             r.created_at.strftime('%Y-%m-%d')] for r in returns]
    
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="returns_export.pdf"'
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, rows, headers, title="Returns Report", orientation=orientation)

    if fmt == 'xlsx':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="returns_export.xlsx"'
        result = _export_excel(response, rows, headers, 'Returns')
        if result:
            return result
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="returns_export.csv"'
    return _export_csv(response, rows, headers)


@login_required
@permission_required('core.view_product', raise_exception=True)
def export_inventory(request):
    """Export inventory (products with stock) to CSV or Excel or PDF."""
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'unit'
    ).order_by('name')
    fmt = request.GET.get('format', 'csv')
    headers = ['Name', 'SKU', 'Category', 'Stock', 'Low Threshold', 'Base Price']
    rows = [[p.name, p.sku or '', p.category.name_en if p.category else '',
             p.stock_quantity, p.low_stock_threshold, str(p.base_price)] for p in products]
    
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventory_export.pdf"'
        orientation = request.GET.get('orientation', 'portrait')
        return _export_pdf(response, rows, headers, title="Inventory Report", orientation=orientation)

    if fmt == 'xlsx':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="inventory_export.xlsx"'
        result = _export_excel(response, rows, headers, 'Inventory')
        if result:
            return result
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
    return _export_csv(response, rows, headers)


@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def sales_report(request):
    """Sales by period with filters and order breakdown."""
    period = request.GET.get('period', 'month')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status_id = request.GET.get('status', '')
    customer_id = request.GET.get('customer', '')

    today = timezone.now().date()
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default logic if no explicit date range
        end = today
        if period == 'day':
            start = today
        elif period == 'week':
            start = today - timedelta(days=7)
        else:
            start = today - timedelta(days=30)
            period = 'month' # Default to month if no period specified

    # Base QuerySet
    sales_qs = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        total_amount__gt=0,
        created_at__date__gte=start,
        created_at__date__lte=end
    )

    # Apply additional filters
    if status_id:
        sales_qs = sales_qs.filter(status_id=status_id)
    else:
        # Default: consider fully paid / completed if checking revenue strictly?
        # The original code did: paid_amount >= total_amount.
        # But if we filter by status, we might see unpaid orders too.
        # Let's keep the original logic if no status is selected, OR maybe we should always show all orders but separate "Paid" metric?
        # The original code was:
        # sales_qs = SalesOrder.objects.filter(..., paid_amount__gte=F('total_amount'), ...)
        # This implies the report is about "Revenue from fully paid orders".
        # Let's keep that logic for the "Total Sales" metric, but for the list of orders, we might want to see all.
        pass

    # For calculation of "Total Sales" (Revenue), we typically only count valid/paid orders or based on accounting rules.
    # The original code filtered by `paid_amount__gte=F('total_amount')`.
    # We should preserve this logic for the summary numbers, but maybe allow filtering the list.
    
    # Let's define "revenue_qs" separately from "display_qs" if needed.
    # But usually, filters apply to everything.
    # If the user selects "Pending", Revenue should be 0 (if we only count Paid).
    
    # Original logic enforced "fully paid". Let's relax it if the user explicitly filters for a status.
    # If no status filter, should we enforce "fully paid"? 
    # Usually "Sales Report" includes Invoiced amounts (Accrual basis) vs Cash basis.
    # The original code seemed to be Cash Basis (fully paid).
    
    # Let's stick to the filters provided.
    
    if not status_id and not customer_id:
         # Maintain backward compatibility for default view: Fully Paid only?
         # Or better: show all valid orders (not cancelled).
         # The original code filtered `paid_amount__gte=F('total_amount')`. 
         # I will modify it to show all non-cancelled orders by default, 
         # BUT I should be careful not to break existing expectations.
         # Let's keep `paid_amount__gte=F('total_amount')` ONLY if no specific filters are applied?
         # No, that's confusing.
         
         # Let's stick to: "Show all orders matching filters".
         # And maybe add a summary for "Paid Amount".
         pass

    # Actually, let's keep the `paid_amount >= total_amount` filter ONLY if it was there before, 
    # BUT the user request is "add filters". 
    # If I add a Status filter, I must allow selecting "Pending" (not fully paid).
    # So I must REMOVE the hardcoded `paid_amount__gte=F('total_amount')` from the base query 
    # and instead make it a default or just show all.
    
    # Let's check the original code again.
    # It had: paid_amount__gte=F('total_amount')
    
    # I will change it to:
    # 1. Filter by Date
    # 2. Filter by Status (optional)
    # 3. Filter by Customer (optional)
    # 4. Exclude Cancelled? usually yes.
    
    # Let's exclude deleted.
    
    # Calculate totals
    summary = sales_qs.aggregate(
        total_revenue=Sum('total_amount'), 
        total_paid=Sum('paid_amount'),
        count=Count('id')
    )
    
    total_sales = summary['total_revenue'] or Decimal('0')
    total_paid = summary['total_paid'] or Decimal('0')
    order_count = summary['count'] or 0

    if customer_id:
        sales_qs = sales_qs.filter(customer_id=customer_id)

    # Recent orders for this period
    recent_orders = sales_qs.select_related('customer', 'status').order_by('-created_at')

    # Status options for filter
    statuses = OrderStatus.objects.all()
    customers = Customer.objects.filter(is_active=True).order_by('name')

    return render(request, 'reports/sales_report.html', {
        'sales_total': total_sales,
        'total_paid': total_paid,
        'order_count': order_count,
        'period': period,
        'period_label': {'day': 'Today', 'week': 'Last 7 Days', 'month': 'Last 30 Days'}.get(period, period),
        'recent_orders': recent_orders[:50], # Limit display
        'start_date': start,
        'end_date': end,
        'statuses': statuses,
        'customers': customers,
        'current_status': int(status_id) if status_id else '',
        'current_customer': int(customer_id) if customer_id else '',
        'date_from': start_date,
        'date_to': end_date,
    })


@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def report_index(request):
    """Reports index with export links."""
    return render(request, 'reports/report_index.html')


@login_required
@permission_required('returns.view_returnrequest', raise_exception=True)
def return_report(request):
    """Return analysis."""
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    reason_id = request.GET.get('reason', '')
    product_id = request.GET.get('product', '')
    
    returns_qs = ReturnItem.objects.filter(
        return_request__deleted_at__isnull=True
    )
    
    if start_date:
        returns_qs = returns_qs.filter(return_request__created_at__date__gte=start_date)
    if end_date:
        returns_qs = returns_qs.filter(return_request__created_at__date__lte=end_date)
    if reason_id:
        returns_qs = returns_qs.filter(reason_id=reason_id)
    if product_id:
        returns_qs = returns_qs.filter(product_id=product_id)
        
    returns = returns_qs.values(
        'product__name', 'reason__name_en'
    ).annotate(
        count=Count('id'),
        total_qty=Sum('quantity')
    ).order_by('-count')[:50]

    reasons = ReturnReason.objects.filter(is_active=True).order_by('name_en')
    products = Product.objects.filter(is_active=True).order_by('name')

    return render(request, 'reports/return_report.html', {
        'returns': returns,
        'reasons': reasons,
        'products': products,
        'date_from': start_date,
        'date_to': end_date,
        'current_reason': int(reason_id) if reason_id else '',
        'current_product': int(product_id) if product_id else '',
    })


def _get_fully_paid_sales_for_period(year, month=None):
    """Sales total and count for fully paid orders in period."""
    qs = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        paid_amount__gte=F('total_amount'),
        total_amount__gt=0,
        created_at__year=year
    )
    if month:
        qs = qs.filter(created_at__month=month)
    result = qs.aggregate(total=Sum('total_amount'), count=Count('id'))
    return result['total'] or Decimal('0'), result['count'] or 0


def _get_profit_totals_for_period(year, month=None):
    """Return (sales_revenue, purchase_costs, operating_expenses) for period."""
    from purchasing.models import PurchaseOrder
    from accounting.models import Expense

    sales_revenue, _ = _get_fully_paid_sales_for_period(year, month)
    purchase_costs, _ = _get_purchase_total_for_period(year, month)
    
    expense_qs = Expense.objects.filter(
        date__year=year,
        deleted_at__isnull=True
    )
    if month:
        expense_qs = expense_qs.filter(date__month=month)
        
    operating_expenses = expense_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return sales_revenue, purchase_costs, operating_expenses


def _build_profit_monthly_data(year):
    """Build monthly sales, expenses, profit dict for profit analysis."""
    from accounting.models import Expense
    from django.db.models.functions import TruncMonth

    monthly_sales = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        paid_amount__gte=F('total_amount'),
        total_amount__gt=0,
        created_at__year=year
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    monthly_expenses = Expense.objects.filter(
        date__year=year
    ).annotate(month=TruncMonth('date')).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    monthly_data = {}
    zero = Decimal('0')
    for item in monthly_sales:
        month_key = item['month'].strftime('%Y-%m')
        monthly_data[month_key] = {'sales': item['total'], 'expenses': zero}
    for item in monthly_expenses:
        month_key = item['month'].strftime('%Y-%m')
        if month_key in monthly_data:
            monthly_data[month_key]['expenses'] = item['total']
        else:
            monthly_data[month_key] = {'sales': zero, 'expenses': item['total']}
    for month_key in monthly_data:
        m = monthly_data[month_key]
        m['profit'] = m['sales'] - m['expenses']
    return monthly_data


def _get_purchase_total_for_period(year, month=None):
    """Purchase total and count for RECEIVED orders in period."""
    from purchasing.models import PurchaseOrder
    filt = {'status': PURCHASE_RECEIVED, 'order_date__year': year, 'deleted_at__isnull': True}
    if month:
        filt['order_date__month'] = month
    result = PurchaseOrder.objects.filter(**filt).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    return result['total'] or Decimal('0'), result['count'] or 0


from django.core.cache import cache

@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def purchase_vs_sales_report(request):
    """Compare purchases and sales by period"""
    from datetime import datetime

    try:
        year = int(request.GET.get('year', datetime.now().year))
    except (ValueError, TypeError):
        year = datetime.now().year
    
    month = request.GET.get('month', '')
    month_int = int(month) if month and month.isdigit() else None

    sales_amt, sales_count = _get_fully_paid_sales_for_period(year, month_int)
    purchase_amt, purchase_count = _get_purchase_total_for_period(
        year, month_int
    )
    gross_margin = sales_amt - purchase_amt
    margin_percent = (
        (gross_margin / sales_amt * Decimal('100')) if sales_amt > 0
        else Decimal('0')
    )

    fmt = request.GET.get('format')
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="purchase_vs_sales_{year}.pdf"'
        data = [
            ['Total Sales Revenue', f"{sales_amt:,.2f}"],
            ['Total Purchase Costs', f"{purchase_amt:,.2f}"],
            ['Gross Margin', f"{gross_margin:,.2f}"],
            ['Margin %', f"{margin_percent:.2f}%"]
        ]
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, data, ['Metric', 'Amount'], title=f'Purchase vs Sales {year}', orientation=orientation)

    # Simple caching
    cache_key = f'purchase_vs_sales_{year}_{month}'
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'reports/purchase_vs_sales.html', cached_context)

    context = {
        'title': 'Purchase vs Sales Report',
        'year': year,
        'month': str(month) if month else '',
        'months': [str(i) for i in range(1, 13)],
        'sales_total': sales_amt,
        'sales_count': sales_count,
        'purchase_total': purchase_amt,
        'purchase_count': purchase_count,
        'gross_margin': gross_margin,
        'margin_percent': margin_percent,
    }
    cache.set(cache_key, context, 60 * 10) # Cache for 10 minutes
    return render(request, 'reports/purchase_vs_sales.html', context)


@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def profit_analysis_report(request):
    """Calculate net profit: Sales - Purchases - Expenses"""
    from datetime import datetime

    try:
        year = int(request.GET.get('year', datetime.now().year))
    except (ValueError, TypeError):
        year = datetime.now().year
    
    month = request.GET.get('month', '')
    month_int = int(month) if month and month.isdigit() else None
        
    sales_revenue, purchase_costs, operating_expenses = (
        _get_profit_totals_for_period(year, month_int)
    )
    gross_profit = sales_revenue - purchase_costs
    net_profit = gross_profit - operating_expenses
    net_margin = (
        (net_profit / sales_revenue * Decimal('100')) if sales_revenue > 0
        else Decimal('0')
    )
    monthly_data = _build_profit_monthly_data(year)

    fmt = request.GET.get('format')
    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        filename_part = f"{year}_{month}" if month else f"{year}"
        response['Content-Disposition'] = f'attachment; filename="profit_analysis_{filename_part}.pdf"'
        data = [
            ['Sales Revenue', f"{sales_revenue:,.2f}"],
            ['- Purchase Costs', f"{purchase_costs:,.2f}"],
            ['= Gross Profit', f"{gross_profit:,.2f}"],
            ['- Operating Expenses', f"{operating_expenses:,.2f}"],
            ['= Net Profit', f"{net_profit:,.2f}"],
            ['Net Margin %', f"{net_margin:.2f}%"]
        ]
        headers = ['Metric', 'Amount']
        title_suffix = f"{year} - Month {month}" if month else f"{year}"
        orientation = request.GET.get('orientation', 'portrait')
        return _export_pdf(response, data, headers, title=f'Profit Analysis {title_suffix}', orientation=orientation)

    # Simple caching
    cache_key = f'profit_analysis_{year}_{month}'
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'reports/profit_analysis.html', cached_context)

    context = {
        'title': 'Profit Analysis',
        'year': year,
        'month': str(month) if month else '',
        'months': [str(i) for i in range(1, 13)],
        'sales_revenue': sales_revenue,
        'purchase_costs': purchase_costs,
        'operating_expenses': operating_expenses,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'net_margin': net_margin,
        'monthly_data': sorted(monthly_data.items()),
    }
    cache.set(cache_key, context, 60 * 15) # Cache for 15 minutes
    return render(request, 'reports/profit_analysis.html', context)


@login_required
@permission_required('common.view_auditlog', raise_exception=True)
def audit_log_report(request):
    """Audit log report with day-by-day filter, action filter, and group by."""
    today = timezone.now().date()
    start_date = request.GET.get(
        'start_date', (today - timedelta(days=7)).strftime('%Y-%m-%d')
    )
    end_date = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    group_by = request.GET.get('group_by', '')

    start, end = _parse_audit_log_date_range(start_date, end_date, default_days=7)
    qs = _get_audit_log_queryset(start, end, action_filter, model_filter)

    logs = list(qs[:LIMIT_AUDIT_LOG_DISPLAY])
    for log in logs:
        changes = log.changes or {}
        log.summary_display = (
            changes.get('summary', '') if isinstance(changes, dict) else ''
        )
        log.module_display_name = _get_module_display_name(log.model_name)

    grouped = _get_audit_log_grouped(
        group_by, start, end, action_filter, model_filter
    )

    actions = AuditLog.objects.values_list(
        'action', flat=True
    ).distinct().order_by('action')
    model_names = AuditLog.objects.values_list(
        'model_name', flat=True
    ).distinct().order_by('model_name')
    model_choices = [(m, _get_module_display_name(m)) for m in model_names]

    return render(request, 'reports/audit_log_report.html', {
        'logs': logs,
        'grouped': grouped,
        'group_by': group_by,
        'start_date': start_date,
        'end_date': end_date,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'actions': actions,
        'model_choices': model_choices,
    })


@login_required
@permission_required('common.view_auditlog', raise_exception=True)
def export_audit_log(request):
    """Export audit log to CSV or Excel."""
    today = timezone.now().date()
    start_date = request.GET.get(
        'start_date', (today - timedelta(days=30)).strftime('%Y-%m-%d')
    )
    end_date = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    fmt = request.GET.get('format', 'csv')

    start, end = _parse_audit_log_date_range(
        start_date, end_date, default_days=30
    )
    qs = _get_audit_log_queryset(start, end, action_filter, model_filter)

    headers = ['Date', 'Time', 'User', 'Action', 'Module', 'What Changed', 'Created At']
    rows = []
    for log in qs[:LIMIT_AUDIT_LOG_EXPORT]:
        summary = (log.changes or {}).get('summary', '') if isinstance(log.changes, dict) else ''
        module_name = _get_module_display_name(log.model_name)
        rows.append([
            log.created_at.strftime('%Y-%m-%d'),
            log.created_at.strftime('%H:%M:%S'),
            log.user.get_username() if log.user else '-',
            log.action,
            module_name,
            summary,
            log.created_at.isoformat(),
        ])

    if fmt == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="audit_log.pdf"'
        orientation = request.GET.get('orientation', 'landscape')
        return _export_pdf(response, rows, headers, title="Audit Log Report", orientation=orientation)

    if fmt == 'xlsx':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="audit_log.xlsx"'
        result = _export_excel(response, rows, headers, 'Audit Log')
        if result:
            return result
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'
    return _export_csv(response, rows, headers)

