"""
Return management models.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import Product
from master_data.models import ReturnReason, ReturnRequestStatus, ReturnType
from orders.models import OrderItem, SalesOrder


from common.models import SoftDeleteMixin


class ReturnRequest(SoftDeleteMixin):
    """Return request linked to original order."""
    order = models.ForeignKey(
        SalesOrder, on_delete=models.PROTECT, related_name='return_requests'
    )
    return_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.ForeignKey(
        ReturnRequestStatus, on_delete=models.PROTECT, related_name='return_requests'
    )
    return_type = models.ForeignKey(
        ReturnType, on_delete=models.PROTECT, related_name='return_requests'
    )
    replacement_order = models.OneToOneField(
        SalesOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='return_request_source', verbose_name=_("Replacement Order")
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Return request")
        verbose_name_plural = _("Return requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['order']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return self.return_number


class ReturnItem(models.Model):
    """Item being returned with reason."""
    return_request = models.ForeignKey(
        ReturnRequest, on_delete=models.CASCADE, related_name='items'
    )
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.PROTECT, related_name='return_items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='return_items'
    )
    quantity = models.PositiveIntegerField()
    reason = models.ForeignKey(
        ReturnReason, on_delete=models.PROTECT, related_name='return_items'
    )
    return_to_stock = models.BooleanField(
        default=True, 
        help_text=_("If checked, items will be added back to stock upon approval.")
    )
    condition_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['return_request', 'id']

    def __str__(self):
        return f"{self.return_request} - {self.product} x {self.quantity}"


class ReturnProcessing(models.Model):
    """Audit trail for return approval/rejection."""
    ACTIONS = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Stock Restored', 'Stock Restored'),
    ]
    return_request = models.ForeignKey(
        ReturnRequest, on_delete=models.CASCADE, related_name='processing_log'
    )
    action = models.CharField(max_length=50, choices=ACTIONS)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='return_processing'
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Return processing log")
        verbose_name_plural = _("Return processing log")
        ordering = ['-processed_at']

    def __str__(self):
        return f"{self.return_request} - {self.action}"
