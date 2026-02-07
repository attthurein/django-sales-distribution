from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator

from .models import ReturnRequest
from .forms import ReturnOrderSelectForm, ReturnCreateForm, ReturnItemFormSet
from .services import (
    create_return_request,
    approve_return as approve_return_service,
    reject_return as reject_return_service,
    formset_to_items_with_reasons,
    create_replacement_order as create_replacement_service,
)
from orders.models import SalesOrder, OrderItem
from master_data.models import OrderStatus, ReturnReason
from master_data.constants import ORDER_DELIVERED, ORDER_PAID
from common.constants import PAGE_SIZE_RETURNS


@login_required
def return_list(request):
    """List all returns with search and filtering"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    returns = ReturnRequest.objects.filter(deleted_at__isnull=True)

    if search_query:
        returns = returns.filter(
            Q(return_number__icontains=search_query) |
            Q(order__customer__name__icontains=search_query) |
            Q(order__customer__phone__icontains=search_query) |
            Q(order__order_number__icontains=search_query)
        )
    if status_filter:
        returns = returns.filter(status__code=status_filter)
    if date_from:
        returns = returns.filter(created_at__date__gte=date_from)
    if date_to:
        returns = returns.filter(created_at__date__lte=date_to)

    returns = returns.select_related(
        'order', 'order__customer', 'status', 'return_type'
    ).prefetch_related(
        'items__product', 'items__order_item'
    ).order_by('-created_at')
    paginator = Paginator(returns, PAGE_SIZE_RETURNS)
    page = request.GET.get('page', 1)
    returns = paginator.get_page(page)

    context = {
        'title': _('ပြန်အပ်မှုများ'),
        'returns': returns,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'returns/return_list.html', context)


@login_required
def return_detail(request, pk):
    """View return details"""
    return_request = get_object_or_404(
        ReturnRequest.objects.filter(deleted_at__isnull=True).select_related(
            'order', 'order__customer', 'status', 'return_type'
        ).prefetch_related(
            'items__product', 'items__order_item',
            'items__reason'
        ),
        pk=pk
    )
    context = {
        'title': _('ပြန်အပ်အသေးစိတ်'),
        'return_request': return_request,
    }
    return render(request, 'returns/return_detail.html', context)


@login_required
@permission_required('returns.delete_returnrequest', raise_exception=True)
def return_delete(request, pk):
    """Soft delete return request - only if PENDING or REJECTED."""
    return_request = get_object_or_404(
        ReturnRequest.objects.filter(deleted_at__isnull=True).select_related('status'),
        pk=pk
    )
    if request.method == 'POST':
        from master_data.constants import RETURN_APPROVED, RETURN_COMPLETED
        if return_request.status.code in (RETURN_APPROVED, RETURN_COMPLETED):
            messages.error(
                request,
                _('Cannot delete approved/completed returns. They affect stock and accounting.')
            )
            return redirect('returns:return_detail', pk=pk)

        with transaction.atomic():
            return_request.deleted_at = timezone.now()
            return_request.save()
        messages.success(request, _('Return deleted successfully.'))
        return redirect('returns:return_list')

    context = {
        'title': _('Delete Return'),
        'return_request': return_request,
    }
    return render(request, 'returns/return_confirm_delete.html', context)


@login_required
@permission_required('returns.add_returnrequest', raise_exception=True)
def return_create(request):
    """Create new return request - step 1: select order"""
    returnable_statuses = OrderStatus.objects.filter(code__in=[ORDER_DELIVERED, ORDER_PAID])
    
    # Get recent returnable orders
    # Note: ModelChoiceField cannot accept a sliced queryset (it calls .get() which fails on slices)
    # So we must fetch the IDs first, then create a fresh unsliced queryset filtered by those IDs.
    base_qs = SalesOrder.objects.filter(
        deleted_at__isnull=True,
        status__in=returnable_statuses,
    ).exclude(
        return_requests__isnull=False,
        return_requests__deleted_at__isnull=True
    ).order_by('-created_at')
    
    recent_ids = list(base_qs.values_list('pk', flat=True)[:20])
    
    orders = SalesOrder.objects.filter(pk__in=recent_ids).select_related('customer').order_by('-created_at')

    form = ReturnOrderSelectForm(
        data=request.POST if request.method == 'POST' else None,
        orders_queryset=orders,
    )
    if request.method == 'POST' and form.is_valid():
        return redirect('returns:return_create_items', order_id=form.cleaned_data['order_id'].pk)
    if request.method == 'POST' and not form.is_valid():
        messages.error(request, _('အမှာစာရွေးချယ်ပါ'))
    context = {
        'title': _('ပြန်အပ်တောင်းဆိုင်းအသစ်ထည့်ရန်'),
        'form': form,
        'orders': orders,
    }
    return render(request, 'returns/return_form.html', context)


@login_required
@permission_required('returns.add_returnrequest', raise_exception=True)
def return_create_items(request, order_id):
    """Create return - step 2: select items and create using formset."""
    order = get_object_or_404(
        SalesOrder.objects.filter(deleted_at__isnull=True).select_related('customer'),
        pk=order_id
    )
    order_items = list(OrderItem.objects.filter(order=order).select_related('product').annotate(
        returned_qty=Coalesce(Sum('return_items__quantity'), Value(0))
    ))
    for item in order_items:
        item.available_to_return = max(
            0, item.quantity - (item.returned_qty or 0)
        )

    initial = [
        {
            'order_item_id': item.id,
            'quantity': 0,
            'reason': None,
            'condition_notes': '',
        }
        for item in order_items
    ]

    form = ReturnCreateForm(
        data=request.POST if request.method == 'POST' else None,
    )
    formset = ReturnItemFormSet(
        data=request.POST if request.method == 'POST' else None,
        initial=initial,
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        items_with_reasons = formset_to_items_with_reasons(formset, order_items)
        if items_with_reasons:
            try:
                ret = create_return_request(
                    order,
                    items_with_reasons,
                    form.cleaned_data['return_type'],
                    form.cleaned_data['notes'] or '',
                )
                messages.success(
                    request, _('ပြန်အပ်တောင်းဆိုင်းအသစ် တည်ဆောက်ပြီး')
                )
                return redirect('returns:return_detail', pk=ret.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(
                request,
                _('ပြန်အပ်ပစ္စည်း အနည်းဆုံး တစ်ခု ရွေးချယ်ပါ')
            )

    context = {
        'order': order,
        'order_items': order_items,
        'form': form,
        'formset': formset,
        'formset_with_items': list(zip(formset, order_items)),
    }
    return render(request, 'returns/return_form_items.html', context)


@login_required
@permission_required('returns.change_returnrequest', raise_exception=True)
def approve_return(request, pk):
    """Approve return request"""
    return_request = get_object_or_404(
        ReturnRequest.objects.filter(deleted_at__isnull=True), pk=pk
    )
    if request.method == 'POST':
        try:
            approve_return_service(
                return_request.id,
                user=request.user if request.user.is_authenticated else None
            )
            messages.success(request, _('ပြန်အပ်တောင်းဆိုင်းခွင့်ပြုပြီးပြီး'))
        except (ValueError, ObjectDoesNotExist) as e:
            messages.error(request, str(e))
        return redirect('returns:return_detail', pk=return_request.pk)
    return redirect('returns:return_detail', pk=return_request.pk)


@login_required
@permission_required('returns.change_returnrequest', raise_exception=True)
def reject_return(request, pk):
    """Reject return request"""
    return_request = get_object_or_404(
        ReturnRequest.objects.filter(deleted_at__isnull=True), pk=pk
    )
    if request.method == 'POST':
        reject_return_service(
            return_request.id,
            user=request.user if request.user.is_authenticated else None
        )
        messages.success(
            request, _('ပြန်အပ်တောင်းဆိုင်းငြင်ပယ်ပြီးပြီး')
        )
        return redirect('returns:return_detail', pk=return_request.pk)
    context = {
        'title': _('ပြန်အပ်တောင်းဆိုင်းငြင်ပယ်ပြီး'),
        'return_request': return_request,
    }
    return render(request, 'returns/return_detail.html', context)


@login_required
@permission_required('orders.add_salesorder', raise_exception=True)
def create_replacement_order(request, pk):
    """Create a 0-price replacement order from a return request."""
    return_request = get_object_or_404(
        ReturnRequest.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    if request.method == 'POST':
        try:
            order = create_replacement_service(return_request, user=request.user)
            messages.success(request, _('Replacement order created successfully.'))
            return redirect('orders:order_detail', pk=order.pk)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"An error occurred while creating replacement order: {str(e)}")
            # Log the error in production
            print(e)
            
    return redirect('returns:return_detail', pk=pk)


@login_required
@permission_required('returns.add_returnrequest', raise_exception=True)
def get_order_items(request):
    """AJAX endpoint to get order items for return"""
    order_id = request.GET.get('order_id')

    try:
        order_items = OrderItem.objects.filter(
            order_id=order_id
        ).select_related('product').annotate(
            returned_qty=Coalesce(Sum('return_items__quantity'), Value(0))
        )

        items_data = []
        for item in order_items:
            items_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'product_id': item.product.id,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'available_quantity': (
                    item.quantity - item.returned_qty
                ),
            })
        
        return JsonResponse({'success': True, 'items': items_data})
    except (ValueError, ObjectDoesNotExist, KeyError) as e:
        return JsonResponse({'success': False, 'message': str(e)})
