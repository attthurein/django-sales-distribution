"""
Order services - create, confirm, deliver, payment, cancel.
Business logic lives here; views stay thin.
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from orders.models import SalesOrder, OrderItem, Payment
from core.models import Product
from core.services import deduct_stock, restore_stock
from master_data.models import OrderStatus
from master_data.constants import (
    ORDER_PENDING,
    ORDER_CONFIRMED,
    ORDER_DELIVERED,
    ORDER_PAID,
    ORDER_CANCELLED,
)


def restore_stock_for_deleted_order(order, user=None):
    """Restore stock for order items when order is deleted. Use core.services."""
    for item in order.orderitem_set.all():
        restore_stock(
            product_id=item.product.id,
            quantity=item.quantity,
            reference_type='SalesOrder',
            reference_id=order.id,
            user=user,
        )


def parse_order_items_from_post(post_data, customer, order_type):
    """
    Parse product_id and quantity from POST data, validate, and build order_items list.
    Returns (order_items, parse_errors, stock_errors).
    """
    product_ids = post_data.getlist('product_id')
    quantities = post_data.getlist('quantity')
    order_items = []
    parse_errors = []
    stock_errors = []

    for i, product_id in enumerate(product_ids):
        if i >= len(quantities) or not quantities[i]:
            parse_errors.append(_('Row %(row)s: quantity is required.') % {'row': i + 1})
            continue
        try:
            quantity = int(quantities[i])
        except (ValueError, TypeError):
            parse_errors.append(_('Row %(row)s: invalid quantity.') % {'row': i + 1})
            continue
        if quantity <= 0:
            parse_errors.append(_('Row %(row)s: quantity must be positive.') % {'row': i + 1})
            continue

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except (ObjectDoesNotExist, ValueError):
            parse_errors.append(
                _('Row %(row)s: product not found or inactive.') % {'row': i + 1}
            )
            continue

        unit_price = product.get_price_for_customer_type(customer.customer_type)
        total_price = quantity * unit_price

        if order_type == 'NORMAL' and quantity > product.stock_quantity:
            stock_errors.append(
                _('Quantity %(qty)s for %(product)s exceeds available stock %(stock)s')
                % {'qty': quantity, 'product': product.name, 'stock': product.stock_quantity}
            )

        order_items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price,
        })

    return order_items, parse_errors, stock_errors


def get_next_order_number():
    """
    Generate order number: PREFIX-YYYYMMDD-NNNN.
    Atomic to prevent collision when multiple requests create orders.
    """
    from django.conf import settings
    prefix = getattr(settings, 'ORDER_NUMBER_PREFIX', 'ORD')
    today = timezone.now().date()
    last_order = SalesOrder.all_objects.filter(
        order_date=today
    ).select_for_update().order_by('-id').first()
    if last_order and last_order.order_number:
        try:
            seq = int(last_order.order_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}-{today.strftime('%Y%m%d')}-{seq:04d}"


def get_outstanding_for_credit_check(customer):
    """Sum of (total_amount - paid_amount) for non-cancelled, non-deleted orders."""
    result = (
        SalesOrder.objects.filter(customer=customer, deleted_at__isnull=True)
        .exclude(status__code=ORDER_CANCELLED)
        .aggregate(total=Sum(F('total_amount') - F('paid_amount')))
    )
    return result['total'] or Decimal('0')


def create_order_from_request(
    customer, order_items, order_type, discount_amount, notes, user=None
):
    """
    Create order with items. Validates stock, credit limit, deducts inventory.
    order_items: list of dict with keys: product, quantity, unit_price, total_price
    order_type: 'NORMAL' or 'PRE_ORDER'
    Returns: SalesOrder. Raises: ValueError on validation failure
    """
    if not order_items:
        raise ValueError("Add at least one product.")

    subtotal = sum(item['total_price'] for item in order_items)
    delivery_fee = customer.township.delivery_fee if customer.township else Decimal('0')
    total_amount = subtotal - Decimal(str(discount_amount)) + delivery_fee

    # Credit limit check (skip if credit_limit is 0 = unlimited)
    if customer.credit_limit and customer.credit_limit > 0:
        outstanding = get_outstanding_for_credit_check(customer)
        if outstanding + total_amount > customer.credit_limit:
            msg = (
                f"Credit limit exceeded. Outstanding: {outstanding}, "
                f"New order: {total_amount}, Limit: {customer.credit_limit}"
            )
            raise ValueError(msg)

    with transaction.atomic():
        pending_status = OrderStatus.get_by_code(ORDER_PENDING)
        order_number = get_next_order_number()

        order = SalesOrder.objects.create(
            customer=customer,
            order_number=order_number,
            order_date=timezone.now().date(),
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            status=pending_status,
            order_type=order_type,
            notes=notes or '',
            created_by=user,
        )

        for item in order_items:
            product = item['product']
            quantity = item['quantity']
            unit_price = item['unit_price']
            total_price = item['total_price']

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )

            if order_type == 'NORMAL':
                deduct_stock(
                    product_id=product.id,
                    quantity=quantity,
                    reference_type='SalesOrder',
                    reference_id=order.id,
                    user=user,
                )

    return order


def update_order_items(order, new_items_data, user=None):
    """
    Update order items (Add/Remove/Update Qty).
    Handles stock deduction/restoration based on changes.
    Re-calculates order totals.
    
    new_items_data: list of dicts from parse_order_items_from_post
    """
    if order.status.code in (ORDER_CONFIRMED, ORDER_DELIVERED, ORDER_PAID, ORDER_CANCELLED):
        raise ValueError(f"Cannot edit items for order in status {order.status.name_en}")

    with transaction.atomic():
        # 1. Map existing items by product_id
        existing_items = {item.product_id: item for item in order.orderitem_set.all()}
        new_items_map = {item['product'].id: item for item in new_items_data}
        
        # 2. Identify removed items -> Restore stock (if NORMAL)
        for product_id, item in existing_items.items():
            if product_id not in new_items_map:
                if order.order_type == 'NORMAL':
                    restore_stock(
                        product_id=product_id,
                        quantity=item.quantity,
                        reference_type='SalesOrder',
                        reference_id=order.id,
                        user=user
                    )
                item.delete()

        # 3. Identify added/updated items
        for product_id, new_data in new_items_map.items():
            product = new_data['product']
            new_qty = new_data['quantity']
            unit_price = new_data['unit_price']
            total_price = new_data['total_price']

            if product_id in existing_items:
                # Update existing
                current_item = existing_items[product_id]
                old_qty = current_item.quantity
                
                if new_qty != old_qty:
                    if order.order_type == 'NORMAL':
                        if new_qty > old_qty:
                            # Increase qty -> Deduct diff
                            deduct_stock(
                                product_id=product_id,
                                quantity=new_qty - old_qty,
                                reference_type='SalesOrder',
                                reference_id=order.id,
                                user=user
                            )
                        else:
                            # Decrease qty -> Restore diff
                            restore_stock(
                                product_id=product_id,
                                quantity=old_qty - new_qty,
                                reference_type='SalesOrder',
                                reference_id=order.id,
                                user=user
                            )
                    
                    current_item.quantity = new_qty
                    current_item.unit_price = unit_price # Update price in case it changed
                    current_item.total_price = total_price
                    current_item.save()
            else:
                # Add new
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=new_qty,
                    unit_price=unit_price,
                    total_price=total_price
                )
                if order.order_type == 'NORMAL':
                    deduct_stock(
                        product_id=product.id,
                        quantity=new_qty,
                        reference_type='SalesOrder',
                        reference_id=order.id,
                        user=user
                    )

        # 4. Recalculate Totals
        # Refresh from DB to get latest items
        items = order.orderitem_set.all()
        subtotal = sum(i.total_price for i in items)
        
        # Recalculate discount (percentage based? currently fixed amount in model)
        # Note: In create_order, discount_amount is passed. 
        # If we have percentage promotion, we should re-apply it.
        # But here we stick to simple logic: preserve discount amount unless it exceeds subtotal?
        # Or better: if applied_promotion exists, re-calculate.
        
        if order.applied_promotion:
            discount_amount = (subtotal * order.applied_promotion.discount_percent / Decimal('100'))
            order.discount_amount = discount_amount
        
        # Delivery fee (might change if customer changed? But here we only edit items)
        # Just use existing logic in save()
        order.subtotal = subtotal
        order.save() # save() triggers total calculation (subtotal - discount + delivery)

    return order


def confirm_order(order_id):
    """Update status to Confirmed."""
    order = SalesOrder.objects.get(id=order_id)
    order.status = OrderStatus.get_by_code(ORDER_CONFIRMED)
    order.save(update_fields=['status'])
    return order


def deliver_order(order_id, user=None):
    """Update status to Delivered, set delivery_date.
    For PRE_ORDER, deduct stock on delivery."""
    order = SalesOrder.objects.prefetch_related('orderitem_set').get(id=order_id)
    with transaction.atomic():
        order.status = OrderStatus.get_by_code(ORDER_DELIVERED)
        order.delivery_date = timezone.now().date()
        if order.order_type == 'PRE_ORDER':
            for item in order.orderitem_set.all():
                deduct_stock(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    reference_type='SalesOrder',
                    reference_id=order.id,
                    user=user,
                )
        order.save(update_fields=['status', 'delivery_date'])
    return order


def process_payment(
    order_id, amount, payment_method=None, reference_number='', notes='', user=None
):
    """Add payment. Signals sync paid_amount and status to PAID when fully paid."""
    order = SalesOrder.objects.get(id=order_id)
    Payment.objects.create(
        order=order,
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
        created_by=user,
    )
    return order


def cancel_order(order_id, user=None):
    """Restore stock and set status to Cancelled.
    Fails if already delivered or paid."""
    order = SalesOrder.objects.prefetch_related('orderitem_set').get(id=order_id)
    delivered = OrderStatus.get_by_code(ORDER_DELIVERED)
    paid = OrderStatus.get_by_code(ORDER_PAID)
    cancelled = OrderStatus.get_by_code(ORDER_CANCELLED)

    if order.status_id in (delivered.id, paid.id):
        raise ValueError(
            "Cannot cancel order that has been delivered or paid"
        )

    with transaction.atomic():
        # Only restore stock for NORMAL orders, as PRE_ORDER deducts on delivery
        # and we block cancellation of delivered orders above.
        if order.order_type == 'NORMAL':
            for item in order.orderitem_set.all():
                restore_stock(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    reference_type='SalesOrder',
                    reference_id=order.id,
                    user=user,
                )
        order.status = cancelled
        order.save(update_fields=['status'])
    return order
