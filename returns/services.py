"""
Return services - create, approve, reject.
"""
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings

from returns.models import ReturnRequest, ReturnItem, ReturnProcessing
from orders.models import SalesOrder, OrderItem
from core.services import restore_stock, deduct_stock
from master_data.models import ReturnRequestStatus, ReturnType, OrderStatus
from master_data.constants import RETURN_PENDING, RETURN_APPROVED, RETURN_REJECTED, RETURN_COMPLETED, ORDER_PENDING
from orders.services import get_next_order_number


def formset_to_items_with_reasons(formset, order_items):
    """
    Convert validated ReturnItemFormSet to items_with_reasons list.
    Used by return_create_items view.
    """
    order_item_map = {item.id: item for item in order_items}
    items_with_reasons = []
    for form in formset:
        if not form.cleaned_data:
            continue
        qty = form.cleaned_data.get('quantity') or 0
        reason = form.cleaned_data.get('reason')
        if qty > 0 and reason:
            order_item_id = form.cleaned_data['order_item_id']
            if order_item_id in order_item_map:
                items_with_reasons.append({
                    'order_item_id': order_item_id,
                    'quantity': qty,
                    'reason_id': reason.id,
                    'return_to_stock': form.cleaned_data.get('return_to_stock', True),
                    'condition_notes': form.cleaned_data.get('condition_notes', ''),
                })
    return items_with_reasons


def _get_next_return_number():
    """Generate return number: RET-YYYY-NNNN."""
    from django.conf import settings
    prefix = getattr(settings, 'RETURN_NUMBER_PREFIX', 'RET')
    year = timezone.now().year
    last = ReturnRequest.objects.filter(
        return_number__startswith=f"{prefix}-{year}-"
    ).order_by('-return_number').values_list('return_number', flat=True).first()
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f"{prefix}-{year}-{seq:04d}"


def create_return_request(order, items_with_reasons, return_type, notes=''):
    """
    Create return request. items_with_reasons: list of dict with
    order_item_id, quantity, reason_id, condition_notes
    """
    from django.conf import settings
    return_days = getattr(settings, 'RETURN_DAYS_LIMIT', 7)

    if not order.delivery_date:
        # Allow return even if delivery_date is not set, assuming status is DELIVERED
        # raise ValueError("Order must be delivered before return")
        pass
    else:
        # Date-only comparison (avoids timezone edge cases)
        today = timezone.now().date()
        days_since = (today - order.delivery_date).days
        if days_since > return_days:
            raise ValueError(f"Return window exceeded. Limit: {return_days} days")

    # Check if active return request exists
    if order.return_requests.filter(deleted_at__isnull=True).exists():
        raise ValueError(_("This order already has a return request."))

    with transaction.atomic():
        pending = ReturnRequestStatus.get_by_code(RETURN_PENDING)
        ret = ReturnRequest.objects.create(
            order=order,
            return_number=_get_next_return_number(),
            status=pending,
            return_type=return_type,
            total_amount=0,
            notes=notes,
        )
        total = 0
        for item_data in items_with_reasons:
            from orders.models import OrderItem
            order_item = OrderItem.objects.get(id=item_data['order_item_id'])
            already_returned = order_item.return_items.aggregate(total=Sum('quantity'))['total'] or 0
            available_to_return = order_item.quantity - already_returned
            if item_data['quantity'] > available_to_return:
                raise ValueError(
                    _("Return quantity exceeds available for %(product)s (max: %(max)s)") % {
                        'product': order_item.product.name,
                        'max': available_to_return
                    }
                )
            ReturnItem.objects.create(
                return_request=ret,
                order_item=order_item,
                product=order_item.product,
                quantity=item_data['quantity'],
                reason_id=item_data['reason_id'],
                return_to_stock=item_data.get('return_to_stock', True),
                condition_notes=item_data.get('condition_notes', ''),
            )
            total += order_item.unit_price * item_data['quantity']
        ret.total_amount = total
        ret.save(update_fields=['total_amount'])
    return ret


def approve_return(return_id, notes='', user=None):
    """Approve return, restore stock."""
    with transaction.atomic():
        ret = ReturnRequest.objects.filter(
            deleted_at__isnull=True
        ).select_for_update().get(id=return_id)
        approved = ReturnRequestStatus.get_by_code(RETURN_APPROVED)
        completed = ReturnRequestStatus.get_by_code(RETURN_COMPLETED)

        ReturnProcessing.objects.create(
            return_request=ret,
            action='Approved',
            notes=notes,
            processed_by=user,
        )

        for item in ret.items.all():
            if item.return_to_stock:
                restore_stock(
                    item.product.id, item.quantity, 'ReturnRequest', ret.id,
                    user=user
                )

        ReturnProcessing.objects.create(
            return_request=ret,
            action='Stock Restored (Partial)' if ret.items.filter(return_to_stock=False).exists() else 'Stock Restored',
            notes=notes,
            processed_by=user,
        )
        ret.status = completed
        ret.save(update_fields=['status'])
    return ret


def reject_return(return_id, notes='', user=None):
    """Reject return."""
    with transaction.atomic():
        ret = ReturnRequest.objects.filter(
            deleted_at__isnull=True
        ).select_for_update().get(id=return_id)
        rejected = ReturnRequestStatus.get_by_code(RETURN_REJECTED)

        ReturnProcessing.objects.create(
            return_request=ret,
            action='Rejected',
            notes=notes,
            processed_by=user,
        )
        ret.status = rejected
        ret.save(update_fields=['status'])
    return ret


def create_replacement_order(return_request, user=None):
    """
    Create a replacement SalesOrder for the returned items.
    The order will have 0 price and type 'REPLACEMENT'.
    """
    if return_request.replacement_order:
        raise ValueError(_("Replacement order already exists for this return."))

    # Validate status? Maybe only allow if approved/completed?
    # For now, allow any non-rejected status if business logic requires flexibility.

    with transaction.atomic():
        # Create Order
        pending_status = OrderStatus.objects.get(code=ORDER_PENDING)
        
        # Use centralized order number generation
        order_number = get_next_order_number()

        new_order = SalesOrder.objects.create(
            customer=return_request.order.customer,
            order_number=order_number,
            order_date=timezone.now().date(),
            status=pending_status,
            order_type='REPLACEMENT',
            created_by=user,
            notes=f"Replacement for Return {return_request.return_number}\n{return_request.notes}"
        )

        # Create Order Items
        for return_item in return_request.items.all():
            OrderItem.objects.create(
                order=new_order,
                product=return_item.product,
                quantity=return_item.quantity,
                unit_price=0,  # Free replacement
                total_price=0
            )
            
            # Deduct stock for replacement items
            deduct_stock(
                product_id=return_item.product.id,
                quantity=return_item.quantity,
                reference_type='SalesOrder',
                reference_id=new_order.id,
                user=user
            )
        
        # Link back
        return_request.replacement_order = new_order
        return_request.save(update_fields=['replacement_order'])
        
        # Log
        ReturnProcessing.objects.create(
            return_request=return_request,
            action='Replacement Created',
            notes=f"Order: {new_order.order_number}",
            processed_by=user,
        )

    return new_order
