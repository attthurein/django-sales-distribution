"""
Purchase order services - receive items, create PO.
"""
from decimal import Decimal
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from purchasing.models import PurchaseOrder, PurchaseItem
from core.services import add_stock
from master_data.constants import PURCHASE_RECEIVED, PURCHASE_ORDERED


def receive_purchase_items(po, received_data, user=None):
    """
    Process received quantities for purchase order items.
    Updates item.received_quantity, uses core.services.add_stock (never update stock directly).

    received_data: list of dicts {'item_id': int, 'quantity': int, 'expiry_date': date|None}
    Raises ValueError on validation failure (e.g. qty exceeds remaining).
    Returns: updated PurchaseOrder
    """
    with transaction.atomic():
        for data in received_data:
            item_id = data['item_id']
            received_qty = data['quantity']
            expiry_date = data.get('expiry_date')

            if received_qty <= 0:
                continue
            item = PurchaseItem.objects.select_for_update().get(id=item_id)
            if item.purchase_order_id != po.id:
                raise ValueError(_("Item does not belong to this purchase order."))
            remaining = item.quantity - item.received_quantity
            if received_qty > remaining:
                raise ValueError(
                    _("Receive qty for %(product)s exceeds remaining (%(remaining)s)") % {
                        'product': item.product.name,
                        'remaining': remaining
                    }
                )
            item.received_quantity += received_qty
            item.save()

            # Update product expiry date if provided
            if expiry_date:
                item.product.expiry_date = expiry_date
                item.product.save(update_fields=['expiry_date'])

            add_stock(
                product_id=item.product_id,
                quantity=received_qty,
                reference_type='PurchaseOrder',
                reference_id=po.id,
                notes=f'Received from PO #{po.id}',
                user=user,
            )

        # Update PO status
        po.refresh_from_db()
        all_items = po.items.all()
        if all(item.received_quantity >= item.quantity for item in all_items):
            po.status = PURCHASE_RECEIVED
        else:
            po.status = PURCHASE_ORDERED
        po.save(update_fields=['status'])

    return po


def create_purchase_order(supplier_id, expected_date, notes, items, user=None):
    """
    Create purchase order with items.
    items: list of (product_id, quantity, unit_cost) tuples
    Returns: PurchaseOrder. Raises ValueError on validation failure.
    """
    if not items:
        raise ValueError(_('Please add at least one item'))

    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            supplier_id=supplier_id,
            expected_date=expected_date if expected_date else None,
            notes=notes or '',
            created_by=user,
        )
        total = Decimal('0')
        for product_id, quantity, unit_cost in items:
            total_cost = quantity * unit_cost
            total += total_cost
            PurchaseItem.objects.create(
                purchase_order=po,
                product_id=product_id,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total_cost,
            )
        po.total_amount = total
        po.save(update_fields=['total_amount'])
    return po


def parse_purchase_items_from_post(post_data):
    """
    Parse product_id, quantity, unit_cost from POST data.
    Returns (items_list, error_msg). items_list is list of (product_id, quantity, unit_cost).
    """
    product_ids = post_data.getlist('product_id[]')
    quantities = post_data.getlist('quantity[]')
    unit_costs = post_data.getlist('unit_cost[]')
    if not product_ids:
        return [], _('Please add at least one item')
    items = []
    for i, product_id in enumerate(product_ids):
        if not product_id or i >= len(quantities) or i >= len(unit_costs):
            continue
        try:
            quantity = int(quantities[i])
            unit_cost = Decimal(str(unit_costs[i]))
        except (ValueError, TypeError):
            return [], _('Invalid quantity or unit cost for item %(i)s') % {'i': i + 1}
        if quantity <= 0 or unit_cost < 0:
            return [], _('Quantity must be positive and unit cost must be non-negative')
        items.append((product_id, quantity, unit_cost))
    if not items:
        return [], _('Please add at least one item')
    return items, None
