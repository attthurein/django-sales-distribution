from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import Product
from master_data.models import Supplier
from common.models import SoftDeleteMixin


class PurchaseOrder(SoftDeleteMixin):
    """Order to supplier"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name='purchase_orders'
    )
    order_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING'
    )
    reference_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Purchase order")
        verbose_name_plural = _("Purchase orders")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expected_date']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"PO #{self.id} - {self.supplier}"


class PurchaseItem(models.Model):
    """Items in a purchase order"""
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    received_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.purchase_order} - {self.product}"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
