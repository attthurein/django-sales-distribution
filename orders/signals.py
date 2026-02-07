"""
Order signals - keep paid_amount in sync with Payment records.
"""
from decimal import Decimal

from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Payment, SalesOrder
from master_data.models import OrderStatus
from master_data.constants import ORDER_PAID


def _sync_order_paid_amount(order):
    """Recalculate paid_amount from payments and update order status."""
    total_paid = order.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    order.paid_amount = total_paid

    update_fields = ['paid_amount']
    if order.paid_amount >= order.total_amount:
        paid_status = OrderStatus.objects.filter(code=ORDER_PAID).first()
        if paid_status and order.status_id != paid_status.id:
            order.status = paid_status
            update_fields.append('status')

    order.save(update_fields=update_fields)


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """Sync order paid_amount when payment is created or updated."""
    _sync_order_paid_amount(instance.order)


@receiver(post_delete, sender=Payment)
def payment_post_delete(sender, instance, **kwargs):
    """Sync order paid_amount when payment is deleted."""
    _sync_order_paid_amount(instance.order)
