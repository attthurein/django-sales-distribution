"""
Customer services - phone validation, outstanding balance.
"""
from decimal import Decimal

from django.db.models import Sum

from orders.models import SalesOrder
from master_data.models import OrderStatus


def validate_phone_unique(phone, exclude_id=None):
    """Check duplicate phone; exclude soft-deleted and current record."""
    from customers.models import Customer
    qs = Customer.objects.filter(phone=phone, deleted_at__isnull=True)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return not qs.exists()


def get_outstanding_balance(customer_id):
    """Sum of unpaid order amounts for credit limit check."""
    paid_status = OrderStatus.objects.filter(code='PAID').first()
    if not paid_status:
        return Decimal('0')

    total = SalesOrder.objects.filter(
        customer_id=customer_id, deleted_at__isnull=True
    ).exclude(status=paid_status).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')

    from orders.models import Payment
    paid = Payment.objects.filter(
        order__customer_id=customer_id,
        order__deleted_at__isnull=True
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    return total - paid
