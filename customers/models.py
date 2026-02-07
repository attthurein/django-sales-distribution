"""
Customer management models.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from master_data.models import CustomerType
from common.models import SoftDeleteMixin


class Customer(SoftDeleteMixin):
    """Customer with credit limit and payment terms."""
    name = models.CharField(max_length=200)
    shop_name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Shop/Store name"),
        help_text=_("For Shop/Distributor - leave blank for Individual")
    )
    contact_person = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Contact person"),
        help_text=_("For Shop/Distributor - leave blank for Individual")
    )
    phone = models.CharField(max_length=20, db_index=True)
    customer_type = models.ForeignKey(
        CustomerType, on_delete=models.PROTECT, related_name='customers'
    )
    township = models.ForeignKey(
        'master_data.Township', on_delete=models.PROTECT, related_name='customers',
        null=True, blank=True
    )
    salesperson = models.ForeignKey(
        'Salesperson', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customers', verbose_name=_("Salesperson")
    )
    street_address = models.TextField(blank=True, verbose_name="Address")
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Maximum credit allowed'
    )
    payment_terms_days = models.PositiveIntegerField(
        default=0,
        help_text='Days until payment due after delivery'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['customer_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Salesperson(SoftDeleteMixin):
    """Sales rep for order assignment."""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salesperson_profile'
)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Salesperson")
        verbose_name_plural = _("Salespeople")
        ordering = ['name']

    def __str__(self):
        return self.name
