from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .models import SalesOrder, Payment
from .forms import OrderUpdateForm, PaymentForm, OrderCreateForm
from .services import (
    create_order_from_request,
    parse_order_items_from_post,
    restore_stock_for_deleted_order,
    update_order_items,
)
from customers.models import Customer
from core.models import Product, ProductPriceTier
from master_data.models import OrderStatus, CustomerType
from master_data.constants import ORDER_CONFIRMED, ORDER_DELIVERED, ORDER_PAID

from common.constants import PAGE_SIZE_ORDERS, LIMIT_CUSTOMER_SEARCH

from .voucher_views import (
    payment_voucher,
    payment_voucher_pdf,
    invoice_view,
    invoice_pdf,
)  # noqa: F401


def _render_order_create_form(request):
    """Render create order form (GET)."""
    preselected = request.GET.get('customer_id', '')
    try:
        initial_customer = int(preselected) if preselected else None
    except (ValueError, TypeError):
        initial_customer = None
    form = OrderCreateForm(initial={
        'customer': initial_customer,
        'discount_amount': Decimal('0'),
    })
    context = {
        'title': _('Create Order'),
        'form': form,
        'products': Product.objects.filter(
            is_active=True
        ).select_related('unit'),
        'customers': Customer.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).select_related('customer_type').order_by('name'),
        'customer_types': CustomerType.objects.all(),
        'preselected_customer': preselected,
    }
    return render(request, 'orders/create.html', context)


def _process_order_create_post(request):
    """
    Process POST for order create. Returns (order, None) on success,
    or (None, response) on validation error (redirect or render).
    """
    form = OrderCreateForm(data=request.POST)
    if not form.is_valid():
        context = {
            'title': _('Create Order'),
            'form': form,
            'products': Product.objects.filter(is_active=True).select_related('unit'),
            'customers': Customer.objects.filter(deleted_at__isnull=True, is_active=True).select_related('customer_type').order_by('name'),
            'customer_types': CustomerType.objects.all(),
            'preselected_customer': '',
        }
        return None, render(request, 'orders/create.html', context)

    customer = form.cleaned_data['customer']
    order_type = 'PRE_ORDER' if form.cleaned_data['is_pre_order'] else 'NORMAL'
    discount_amount = form.cleaned_data['discount_amount'] or Decimal('0')
    notes = form.cleaned_data.get('notes') or ''

    product_ids = request.POST.getlist('product_id')
    quantities = request.POST.getlist('quantity')
    if not product_ids or not quantities:
        messages.error(request, _('Add at least one product.'))
        return None, redirect('orders:order_create')

    order_items, parse_errors, stock_errors = parse_order_items_from_post(
        request.POST, customer, order_type
    )

    if parse_errors or not order_items or stock_errors:
        for err in (parse_errors or []):
            messages.error(request, err)
        if not order_items:
            messages.error(request, _('Add at least one valid product.'))
        for err in (stock_errors or []):
            messages.error(request, err)
        context = {
            'title': _('Create Order'),
            'form': form,
            'products': Product.objects.filter(is_active=True).select_related('unit'),
            'customers': Customer.objects.filter(deleted_at__isnull=True, is_active=True).select_related('customer_type').order_by('name'),
            'customer_types': CustomerType.objects.all(),
            'preselected_customer': '',
        }
        return None, render(request, 'orders/create.html', context)

    try:
        order = create_order_from_request(
            customer=customer,
            order_items=order_items,
            order_type=order_type,
            discount_amount=discount_amount,
            notes=notes,
            user=request.user if request.user.is_authenticated else None,
        )
    except ValueError as e:
        messages.error(
            request,
            _('Error creating order: %(error)s') % {'error': str(e)}
        )
        context = {
            'title': _('Create Order'),
            'form': form,
            'products': Product.objects.filter(is_active=True).select_related('unit'),
            'customers': Customer.objects.filter(deleted_at__isnull=True, is_active=True).select_related('customer_type').order_by('name'),
            'customer_types': CustomerType.objects.all(),
            'preselected_customer': '',
        }
        return None, render(request, 'orders/create.html', context)

    return order, None


@login_required
def order_list(request):
    """List all orders with search and filtering"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    order_type_filter = request.GET.get('order_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    orders = SalesOrder.objects.filter(deleted_at__isnull=True)

    if order_type_filter:
        orders = orders.filter(order_type=order_type_filter)
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__name__icontains=search_query)
        )
    if status_filter:
        orders = orders.filter(status__code=status_filter)
    if customer_filter:
        orders = orders.filter(customer_id=customer_filter)
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    orders = orders.select_related('customer', 'status', 'created_by').order_by('-created_at')
    paginator = Paginator(orders, PAGE_SIZE_ORDERS)
    page = request.GET.get('page', 1)
    orders = paginator.get_page(page)

    context = {
        'title': _('Orders'),
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'order_type_filter': order_type_filter,
        'date_from': date_from,
        'date_to': date_to,
        'customer_filter': customer_filter,
        'customers': Customer.objects.filter(deleted_at__isnull=True, is_active=True).order_by('name'),
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, pk):
    """View order details. Excludes soft-deleted orders."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True)
        .select_related('customer', 'created_by', 'status')
        .prefetch_related('orderitem_set__product', 'payments__payment_method'),
        pk=pk
    )
    total_paid = sum(p.amount for p in order.payments.all())
    context = {
        'title': _('Order Detail'),
        'order': order,
        'total_paid': total_paid,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@permission_required('orders.add_salesorder', raise_exception=True)
def order_create(request):
    """Create new order - delegates to service layer."""
    if request.method != 'POST':
        return _render_order_create_form(request)

    order, redirect_resp = _process_order_create_post(request)
    if redirect_resp is not None:
        return redirect_resp

    messages.success(request, _('Order created successfully.'))
    return redirect('orders:order_detail', pk=order.pk)


@login_required
@permission_required('orders.change_salesorder', raise_exception=True)
def order_update(request, pk):
    """Update order status, delivery date, notes AND items."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True).select_related('customer', 'status').prefetch_related('orderitem_set__product'),
        pk=pk
    )

    # Immutable invoice rule: block status changes for delivered/paid orders
    is_locked = order.status and order.status.code in (ORDER_DELIVERED, ORDER_PAID)

    if request.method == 'POST':
        form = OrderUpdateForm(
            data=request.POST,
            instance=order,
        )
        if is_locked:
            # Only allow notes/delivery_date edit, not status
            form.fields['status'].disabled = True
        
        if form.is_valid():
            # Validate items if not locked
            order_items = []
            items_valid = True
            
            if not is_locked:
                product_ids = request.POST.getlist('product_id')
                if not product_ids:
                    messages.error(request, _('Order must have at least one product.'))
                    items_valid = False
                else:
                    # Note: parse_order_items_from_post checks current stock.
                    # For updates, we might be increasing quantity of an existing item.
                    # The parse function checks `quantity > product.stock_quantity`.
                    # But if we already hold 5 and want 6, we only need 1 more.
                    # The parse function is slightly too strict for updates if it checks absolute quantity against stock.
                    # Let's check `orders/services.py` again.
                    # Yes: `if order_type == 'NORMAL' and quantity > product.stock_quantity:`
                    # This check is WRONG for updates if we already have some stock reserved.
                    # However, fixing `parse_order_items_from_post` might break create?
                    # No, for create it's fine.
                    # For update, we should skip stock check in parser and let `update_order_items` (via `deduct_stock`) handle it?
                    # Or we calculate the delta and check that?
                    # Let's try to proceed, but be aware of this limitation.
                    # Actually `deduct_stock` handles validation correctly.
                    # We can ignore `stock_errors` from parser for updates and rely on `update_order_items`?
                    # But `parse_order_items_from_post` returns errors.
                    
                    # Workaround: We use a modified parser or just manual parsing here?
                    # Or we accept that we can't update to 10 if we have 5 and stock is 5 (total 10 needed, 5 in stock).
                    # If we hold 5, stock shows 5 (because we deducted).
                    # So if we want 10, we need 5 more. Stock has 5.
                    # If parser checks 10 > 5 -> Error.
                    # But actually it is allowed.
                    
                    # So `parse_order_items_from_post` is NOT suitable for updates as is.
                    # I'll just parse manually here or use the parser but ignore stock errors, 
                    # relying on `update_order_items` to catch them.
                    
                    order_items, parse_errors, stock_errors = parse_order_items_from_post(
                        request.POST, order.customer, order.order_type
                    )
                    # We ignore stock_errors from parser because it doesn't know about currently held stock.
                    
                    if parse_errors:
                        for err in parse_errors: messages.error(request, err)
                        items_valid = False

            if items_valid:
                try:
                    with transaction.atomic():
                        if is_locked:
                            # Preserve status, only update notes and delivery_date
                            order.delivery_date = form.cleaned_data['delivery_date']
                            order.notes = form.cleaned_data['notes']
                            order.save(update_fields=['delivery_date', 'notes'])
                        else:
                            form.save()
                            update_order_items(order, order_items, user=request.user)
                            
                        messages.success(request, _('Order updated successfully.'))
                        return redirect('orders:order_detail', pk=order.pk)
                except ValueError as e:
                    messages.error(request, str(e))
    else:
        form = OrderUpdateForm(instance=order)
        if is_locked:
            form.fields['status'].disabled = True

    context = {
        'title': _('Edit Order'),
        'order': order,
        'form': form,
        'is_locked': is_locked,
        'products': Product.objects.filter(is_active=True).select_related('unit'),
        'existing_items': order.orderitem_set.all(),
    }
    return render(request, 'orders/order_form.html', context)


@login_required
@permission_required('orders.change_salesorder', raise_exception=True)
def order_confirm(request, pk):
    """Confirm order"""
    order = get_object_or_404(SalesOrder.objects.filter(deleted_at__isnull=True), pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                order.status = OrderStatus.get_by_code(ORDER_CONFIRMED)
                order.save(update_fields=['status'])
            messages.success(request, _('Order confirmed successfully.'))
        except ObjectDoesNotExist:
            messages.error(request, _('Status CONFIRMED not found'))
    return redirect('orders:order_detail', pk=pk)


@login_required
@permission_required('orders.change_salesorder', raise_exception=True)
def order_deliver(request, pk):
    """Mark order as delivered. For PRE_ORDER, deduct stock on delivery."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True).prefetch_related('orderitem_set'),
        pk=pk
    )
    if request.method == 'POST':
        try:
            from .services import deliver_order
            deliver_order(order_id=pk, user=request.user if request.user.is_authenticated else None)
            messages.success(request, _('Order delivered successfully.'))
        except ObjectDoesNotExist:
            messages.error(request, _('Status DELIVERED not found'))
    return redirect('orders:order_detail', pk=pk)


@login_required
@permission_required('orders.change_salesorder', raise_exception=True)
def order_cancel(request, pk):
    """Cancel order (change status to Cancelled)."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    if request.method == 'POST':
        try:
            from .services import cancel_order as service_cancel_order
            service_cancel_order(order_id=pk, user=request.user if request.user.is_authenticated else None)
            messages.success(request, _('Order cancelled successfully.'))
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, _('Error cancelling order: %(error)s') % {'error': str(e)})
            
    return redirect('orders:order_detail', pk=pk)


@login_required
@permission_required('orders.delete_salesorder', raise_exception=True)
def order_delete(request, pk):
    """Soft delete order - sets deleted_at and restores stock."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True).prefetch_related(
            'orderitem_set', 'payments', 'return_requests'
        ),
        pk=pk
    )

    if request.method == 'POST':
        # Block deletion if order has payments or return requests
        if order.payments.exists():
            messages.error(
                request,
                _('Cannot delete order with payments. Refund or void payments first.')
            )
            return redirect('orders:order_detail', pk=order.pk)
        if order.return_requests.exists():
            messages.error(
                request,
                _('Cannot delete order with return requests. Process or cancel returns first.')
            )
            return redirect('orders:order_detail', pk=order.pk)

        user = request.user if request.user.is_authenticated else None
        with transaction.atomic():
            if order.order_type == 'NORMAL':
                restore_stock_for_deleted_order(order, user)
            elif order.order_type == 'PRE_ORDER' and order.delivery_date:
                restore_stock_for_deleted_order(order, user)
            order.soft_delete()
        messages.success(request, _('Order deleted successfully.'))
        return redirect('orders:order_list')
    
    context = {
        'title': _('Delete Order'),
        'order': order,
    }
    return render(request, 'orders/delete.html', context)


@login_required
def quick_customer_search(request):
    """AJAX endpoint for quick customer search"""
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        return JsonResponse({'customers': []})
    
    customers = Customer.objects.filter(
        deleted_at__isnull=True, is_active=True
    ).filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query)
    ).select_related('customer_type')[:LIMIT_CUSTOMER_SEARCH]
    
    customer_data = []
    for customer in customers:
        ct = customer.customer_type
        customer_data.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'customer_type_id': ct.id if ct else None,
            'customer_type_name': ct.name_en if ct else '',
            'display_name': customer.name,
        })
    
    return JsonResponse({'customers': customer_data})


@login_required
def product_prices_by_customer(request):
    """AJAX endpoint to get all product prices for a specific customer"""
    customer_id = request.GET.get('customer_id')
    if not customer_id:
        return JsonResponse({'prices': {}})
    
    try:
        customer = Customer.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).get(pk=customer_id)
        
        products = Product.objects.filter(is_active=True)
        # Pre-fetch price tiers for this customer type to avoid N+1
        price_tiers = {
            pt.product_id: pt.price 
            for pt in ProductPriceTier.objects.filter(customer_type=customer.customer_type)
        }
        
        prices = {}
        for product in products:
            price = price_tiers.get(product.id, product.base_price)
            prices[product.id] = str(price)
            
        return JsonResponse({'prices': prices})
    except Customer.DoesNotExist:
        return JsonResponse({'prices': {}})


@login_required
def get_product_info(request):
    """AJAX endpoint to get product info"""
    product_id = request.GET.get('product_id')
    customer_type_id = request.GET.get('customer_type_id', '')
    
    try:
        product = Product.objects.select_related('unit').get(pk=product_id, is_active=True)
        customer_type = CustomerType.objects.filter(pk=customer_type_id).first() if customer_type_id else None
        unit_display = product.unit.name_en if product.unit else ''
        
        return JsonResponse({
            'success': True,
            'unit_price': str(product.get_price_for_customer_type(customer_type)),
            'current_stock': product.current_stock,
            'unit_type': unit_display,
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})


@login_required
@permission_required('orders.add_payment', raise_exception=True)
def add_payment(request, pk):
    """Add payment to existing order using ModelForm."""
    order = get_object_or_404(SalesOrder.objects.filter(deleted_at__isnull=True), pk=pk)

    form = PaymentForm(
        data=request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            payment = form.save(commit=False)
            payment.order = order
            payment.payment_date = timezone.now().date()
            payment.created_by = request.user if request.user.is_authenticated else None
            payment.save()
        messages.success(request, _('Payment recorded successfully.'))
        return redirect('orders:order_detail', pk=order.pk)

    context = {
        'title': _('Add Payment'),
        'order': order,
        'form': form,
    }
    return render(request, 'orders/order_payment.html', context)
