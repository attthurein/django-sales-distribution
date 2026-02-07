"""
Core models - Product & Inventory.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from master_data.models import CustomerType, ProductCategory, UnitOfMeasure
from common.models import SoftDeleteMixin
from common.constants import LIMIT_EXPIRY_DAYS


class Product(SoftDeleteMixin):
    """Product with category, unit, pricing, stock."""
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    sku = models.CharField(max_length=100, unique=True, blank=True, verbose_name=_("SKU"))
    category = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT, null=True, blank=True,
        related_name='products', verbose_name=_("Category")
    )
    unit = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, null=True, blank=True,
        related_name='products', verbose_name=_("Unit")
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Base Price"))
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='For margin calculation', verbose_name=_("Cost Price")
    )
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name=_("Stock Quantity"))
    low_stock_threshold = models.PositiveIntegerField(default=10, verbose_name=_("Low Stock Threshold"))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Expiry Date"))
    expiry_alert_days = models.PositiveIntegerField(
        default=LIMIT_EXPIRY_DAYS,
        help_text=_('Days before expiry to trigger alert'),
        verbose_name=_("Expiry Alert Days")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['name']),
            models.Index(fields=['sku']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(base_price__gte=0), name='product_base_price_gte_0'),
            models.CheckConstraint(check=models.Q(cost_price__gte=0) | models.Q(cost_price__isnull=True), name='product_cost_price_gte_0'),
            models.CheckConstraint(check=models.Q(stock_quantity__gte=0), name='product_stock_quantity_gte_0'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def current_stock(self):
        """Alias for stock_quantity for compatibility."""
        return self.stock_quantity

    def get_price_for_customer_type(self, customer_type):
        """Get price from ProductPriceTier or base price for given customer type."""
        tier = ProductPriceTier.objects.filter(
            product=self, customer_type=customer_type
        ).first()
        return tier.price if tier else self.base_price


class ProductVariant(SoftDeleteMixin):
    """Size, color variants of a product."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants'
    )
    name = models.CharField(max_length=100)  # e.g. Size M, Red
    sku_suffix = models.CharField(max_length=50, blank=True)
    price_adjustment = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Added to base price (can be negative)'
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Product variant")
        verbose_name_plural = _("Product variants")
        unique_together = ['product', 'name']
        ordering = ['product', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductPriceTier(models.Model):
    """Price per product per customer type."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='price_tiers'
    )
    customer_type = models.ForeignKey(
        CustomerType, on_delete=models.PROTECT, related_name='price_tiers'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ['product', 'customer_type']
        ordering = ['product', 'customer_type']

    def __str__(self):
        return f"{self.product} - {self.customer_type}: {self.price}"


class Batch(SoftDeleteMixin):
    """Batch/Lot for FMCG tracking."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='batches'
    )
    batch_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Batch")
        verbose_name_plural = _("Batches")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.product} - {self.batch_number}"

    def save(self, *args, **kwargs):
        """Save batch. Stock updates go through core.services (don't update stock directly)."""
        from django.db import transaction
        from django.utils import timezone
        from core.services import add_stock_from_batch, adjust_stock_from_batch

        creating = self.pk is None
        old_quantity = None
        if not creating:
            old = type(self).objects.get(pk=self.pk)
            old_quantity = old.quantity

        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating:
                add_stock_from_batch(
                    product_id=self.product_id,
                    quantity=self.quantity,
                    batch_id=self.id,
                    reference_id=self.id,
                )
            elif old_quantity is not None and self.quantity != old_quantity:
                delta = self.quantity - old_quantity
                adjust_stock_from_batch(
                    product_id=self.product_id,
                    quantity_delta=delta,
                    batch_id=self.id,
                    reference_id=self.id,
                )
            
            # Sync product expiry date to the earliest batch expiry with stock
            today = timezone.now().date()
            earliest_batch = Batch.objects.filter(
                product=self.product,
                quantity__gt=0,
                expiry_date__isnull=False,
                expiry_date__gte=today
            ).order_by('expiry_date').first()
            
            if earliest_batch:
                self.product.expiry_date = earliest_batch.expiry_date
                self.product.save(update_fields=['expiry_date'])

class StockMovement(models.Model):
    """All inventory changes with audit trail."""
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return'),
    ]
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='stock_movements'
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for IN/RETURN, negative for OUT
    reference_type = models.CharField(max_length=50, blank=True)  # e.g. Order, Return
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )

    class Meta:
        verbose_name = _("Stock movement")
        verbose_name_plural = _("Stock movements")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['movement_type']),
        ]

    def __str__(self):
        return f"{self.product} - {self.movement_type} - {self.quantity}"