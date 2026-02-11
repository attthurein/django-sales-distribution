"""
Dashboard views.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.cache import cache

from orders.models import SalesOrder, OrderItem, Payment
from core.models import Product, StockMovement
from core.services import check_low_stock
from returns.models import ReturnRequest
from master_data.models import OrderStatus
from master_data.constants import (
    ORDER_PENDING,
    ORDER_CONFIRMED,
    ORDER_DELIVERED,
)

from common.constants import (
    LIMIT_RECENT_ORDERS,
    LIMIT_RECENT_RETURNS,
    LIMIT_RECENT_MOVEMENTS,
    LIMIT_LOW_STOCK_DISPLAY,
    LIMIT_EXPIRY_DAYS,
    LIMIT_EXPIRY_URGENT_DAYS,
)


def _get_today_sales(today):
    """Today's sales - actual payments received today."""
    return Payment.objects.filter(
        payment_date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')


def _get_pending_orders():
    """Count of pending and confirmed orders."""
    pending_status = OrderStatus.objects.filter(code=ORDER_PENDING).first()
    confirmed_status = OrderStatus.objects.filter(code=ORDER_CONFIRMED).first()
    statuses = [s for s in [pending_status, confirmed_status] if s]
    if not statuses:
        return 0
    return SalesOrder.objects.filter(deleted_at__isnull=True, status__in=statuses).count()


def _get_overdue_count():
    """Count of delivered but not paid orders (overdue payments)."""
    delivered_status = OrderStatus.objects.filter(code=ORDER_DELIVERED).first()
    if not delivered_status:
        return 0
    return SalesOrder.objects.filter(
        deleted_at__isnull=True,
        status=delivered_status,
        delivery_date__isnull=False,
        paid_amount__lt=F('total_amount')
    ).count()


def _get_expiry_alert(today):
    """Count of products expiring within their specific alert threshold."""
    # Fetch relevant fields for all active products with expiry dates
    # We iterate in Python to handle per-product alert days (dynamic duration)
    # This avoids database-specific interval arithmetic logic
    products = Product.objects.filter(
        is_active=True,
        expiry_date__isnull=False,
        expiry_date__gte=today
    ).values('expiry_date', 'expiry_alert_days')

    count = 0
    for p in products:
        # Check if today is within the alert window
        # Alert starts at: expiry_date - alert_days
        # So: today >= expiry_date - alert_days
        # Which means: expiry_date <= today + alert_days
        limit_date = today + timedelta(days=p['expiry_alert_days'])
        if p['expiry_date'] <= limit_date:
            count += 1
            
    return count


def _build_dashboard_queries(today):
    """Build querysets for dashboard metrics and lists."""
    low_stock_qs = (
        check_low_stock()
        .select_related('category')
        .order_by('stock_quantity')
    )
    recent_returns_qs = ReturnRequest.objects.filter(
        deleted_at__isnull=True
    ).select_related(
        'order', 'status'
    ).order_by('-created_at')[:LIMIT_RECENT_RETURNS]
    recent_orders_qs = SalesOrder.objects.filter(
        deleted_at__isnull=True
    ).select_related('customer', 'status').order_by('-created_at')[:LIMIT_RECENT_ORDERS]
    recent_movements_qs = StockMovement.objects.select_related(
        'product'
    ).order_by('-created_at')[:LIMIT_RECENT_MOVEMENTS]
    products_with_stock_qs = Product.objects.filter(
        is_active=True
    ).select_related('category').order_by('name')[:20]
    stock_by_category_qs = Product.objects.filter(
        is_active=True
    ).values('category__name_en', 'category__name_my').annotate(
        total=Sum('stock_quantity')
    ).order_by('category__name_en')
    return {
        'low_stock_qs': low_stock_qs,
        'recent_returns_qs': recent_returns_qs,
        'recent_orders_qs': recent_orders_qs,
        'recent_movements_qs': recent_movements_qs,
        'products_with_stock_qs': products_with_stock_qs,
        'stock_by_category_qs': stock_by_category_qs,
    }


def _get_expiring_by_shop(today):
    """Products expiring soon, grouped by customer."""
    two_days = today + timedelta(days=LIMIT_EXPIRY_URGENT_DAYS)
    delivered_status = OrderStatus.objects.filter(code=ORDER_DELIVERED).first()
    exp_products = Product.objects.filter(
        is_active=True,
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=two_days
    )

    if not delivered_status or not exp_products.exists():
        return []

    relevant_items = (
        OrderItem.objects.filter(
            product__in=exp_products,
            order__deleted_at__isnull=True,
            order__status=delivered_status
        )
        .values(
            'product__name',
            'product__expiry_date',
            'order__customer__name',
            'order__customer__phone'
        )
        .annotate(
            ordered=Sum('quantity'),
            returned=Coalesce(Sum('return_items__quantity'), 0)
        )
    )

    expiring_by_shop = []
    for item in relevant_items:
        remaining = (item['ordered'] or 0) - (item['returned'] or 0)
        if remaining > 0:
            expiring_by_shop.append({
                'product_name': item['product__name'],
                'expiry_date': item['product__expiry_date'],
                'customer_name': item['order__customer__name'],
                'phone': item['order__customer__phone'],
                'remaining': remaining,
                'days_left': (item['product__expiry_date'] - today).days,
            })

    return sorted(
        expiring_by_shop,
        key=lambda x: (x['expiry_date'], x['product_name'])
    )


@login_required
@permission_required('orders.view_salesorder', raise_exception=True)
def index(request):
    """Dashboard with real-time metrics."""
    today = timezone.now().date()
    
    # Cache key based on date to ensure fresh data for new day
    cache_key = f'dashboard_stats_{today}'
    stats = cache.get(cache_key)
    
    if not stats:
        # Expensive aggregations
        today_sales = _get_today_sales(today)
        yesterday_sales = _get_today_sales(today - timedelta(days=1))
        
        # Calculate percentage change
        sales_growth = 0
        if yesterday_sales > 0:
            sales_growth = ((today_sales - yesterday_sales) / yesterday_sales) * 100
        elif today_sales > 0:
            sales_growth = 100
        else:
            sales_growth = 0
            
        stats = {
            'today_sales': today_sales,
            'sales_growth': sales_growth,
            'pending_orders': _get_pending_orders(),
            'overdue_count': _get_overdue_count(),
            'expiry_alert': _get_expiry_alert(today),
        }
        # Cache for 15 minutes
        cache.set(cache_key, stats, 60 * 15)

    qs = _build_dashboard_queries(today)

    # Prepare stock chart data with localized labels
    stock_chart_data = []
    lang = request.LANGUAGE_CODE
    for item in qs['stock_by_category_qs']:
        label = item['category__name_my'] if lang == 'my' and item.get('category__name_my') else item.get('category__name_en') or '-'
        stock_chart_data.append({
            'label': label,
            'value': float(item['total'] or 0)
        })

    context = {
        'today_sales': stats['today_sales'],
        'sales_growth': stats['sales_growth'],
        'pending_orders': stats['pending_orders'],
        'low_stock_count': qs['low_stock_qs'].count(),
        'low_stock_products': qs['low_stock_qs'][:LIMIT_LOW_STOCK_DISPLAY],
        'recent_returns': qs['recent_returns_qs'],
        'overdue_count': stats['overdue_count'],
        'expiry_alert': stats['expiry_alert'],
        'recent_orders': qs['recent_orders_qs'],
        'recent_movements': qs['recent_movements_qs'],
        'products_with_stock': qs['products_with_stock_qs'],
        'stock_by_category': qs['stock_by_category_qs'],
        'stock_chart_data': stock_chart_data,
        'expiring_by_shop': _get_expiring_by_shop(today),
    }
    return render(request, 'dashboard/index.html', context)


class LowStockLoginView(LoginView):
    """Custom login that warns about low stock after successful login."""
    def form_valid(self, form):
        response = super().form_valid(form)
        low = check_low_stock().order_by('stock_quantity')[:10]
        if low:
            names = [f"{p.name} ({p.stock_quantity})" for p in low]
            msg = gettext("Low stock: %(products)s") % {
                'products': ", ".join(names)
            }
            messages.warning(self.request, msg)
        return response
