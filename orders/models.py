from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F
from customers.models import Customer
from core.models import Product
from master_data.models import OrderStatus, Promotion
from common.models import SoftDeleteMixin


class SalesOrder(SoftDeleteMixin):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name=_("Customer"))
    order_number = models.CharField(_("Order number"), max_length=50, unique=True)
    order_date = models.DateField(_("Order date"), default=timezone.now)
    delivery_date = models.DateField(_("Delivery date"), null=True, blank=True)
    
    # Pricing
    subtotal = models.DecimalField(_("Subtotal"), max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("Discount"), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Total amount"), max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid amount"), max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(_("Delivery fee"), max_digits=10, decimal_places=2, default=0)
    applied_promotion = models.ForeignKey(
        'master_data.Promotion', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Promotion")
    )
    
    # Order type: NORMAL (from stock), PRE_ORDER (pre-order, stock not deducted until delivery)
    ORDER_TYPE_CHOICES = [
        ('NORMAL', _('Normal')),
        ('PRE_ORDER', _('Pre-order')),
        ('REPLACEMENT', _('Replacement')),
    ]
    order_type = models.CharField(
        max_length=20, choices=ORDER_TYPE_CHOICES, default='NORMAL',
        verbose_name=_("Order type")
    )

    # Status
    status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT, verbose_name=_("Status"), null=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Tracking
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name=_("Recorded by"))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Sales Orders")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['order_type']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['delivery_date']),
        ]

    def __str__(self):
        return self.order_number

    def get_status_display_my(self):
        """Get Myanmar display for status"""
        if self.status:
            return self.status.name_my
        return ""

    def get_balance_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.paid_amount

    def is_paid(self):
        """Check if order is fully paid"""
        return self.paid_amount >= self.total_amount

    def is_partially_paid(self):
        """Check if order is partially paid"""
        return 0 < self.paid_amount < self.total_amount

    def get_total_items(self):
        """Get total number of items"""
        return self.orderitem_set.aggregate(total=Sum('quantity'))['total'] or 0

    def soft_delete(self):
        """Prevent deleting active orders to protect stock integrity."""
        from django.core.exceptions import ValidationError
        from master_data.constants import ORDER_PENDING, ORDER_CANCELLED
        
        if self.status and self.status.code not in [ORDER_PENDING, ORDER_CANCELLED]:
            raise ValidationError(
                _("Cannot delete order in '%(status)s' status. Please cancel it first to restore stock.") 
                % {'status': self.status.name_en}
            )
        super().soft_delete()

    def save(self, *args, **kwargs):
        """Auto-calculate delivery fee and apply promotions"""
        # Skip auto-calculations for replacement orders
        if self.order_type == 'REPLACEMENT':
            super().save(*args, **kwargs)
            return

        # Calculate delivery fee from customer's township
        if self.customer and self.customer.township and not self.delivery_fee:
            self.delivery_fee = self.customer.township.delivery_fee
        
        # Apply best active promotion if not already applied
        if not self.applied_promotion:
            today = timezone.now().date()
            active_promotions = Promotion.objects.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            ).order_by('-discount_percent')

            # Optimize: Use slice to get first item in one query instead of exists() + first()
            best_promotion = active_promotions.first()
            if best_promotion:
                self.applied_promotion = best_promotion
                # Apply discount to subtotal (use Decimal for precision)
                if self.subtotal > 0:
                    discount = (
                        self.subtotal * self.applied_promotion.discount_percent / Decimal('100')
                    )
                    self.discount_amount = discount
        
        # Recalculate total with delivery fee
        self.total_amount = self.subtotal - self.discount_amount + self.delivery_fee
        
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, verbose_name=_("Order"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    quantity = models.IntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(_("Unit price"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("Total"), max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Order item")
        verbose_name_plural = _("Order items")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Auto-calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(SoftDeleteMixin):
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, verbose_name=_("Order"), related_name='payments')
    voucher_number = models.CharField(_("Voucher number"), max_length=50, unique=True, db_index=True, null=True, blank=True)
    payment_date = models.DateField(_("Payment date"), default=timezone.now)
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(
        'master_data.PaymentMethod', 
        on_delete=models.PROTECT, 
        verbose_name=_("Payment method"),
        related_name='payments',
        null=True, blank=True
    )
    reference_number = models.CharField(_("Reference number"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='payments_created')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['voucher_number']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.voucher_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Auto-generate voucher number if not set (atomic to prevent collision)
        if not self.voucher_number:
            today = timezone.now().date()
            with transaction.atomic():
                last = Payment.objects.filter(
                    payment_date=today
                ).select_for_update().order_by('-id').first()
                if last and last.voucher_number:
                    try:
                        seq = int(last.voucher_number.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                self.voucher_number = f"PV-{today.strftime('%Y%m%d')}-{seq:04d}"
        super().save(*args, **kwargs)
