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
    name = models.CharField(max_length=200, verbose_name=_("Name"))
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
    phone = models.CharField(max_length=20, db_index=True, verbose_name=_("Phone"))
    customer_type = models.ForeignKey(
        CustomerType, on_delete=models.PROTECT, related_name='customers',
        verbose_name=_("Customer Type")
    )
    township = models.ForeignKey(
        'master_data.Township', on_delete=models.PROTECT, related_name='customers',
        null=True, blank=True, verbose_name=_("Township")
    )
    salesperson = models.ForeignKey(
        'Salesperson', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customers', verbose_name=_("Salesperson")
    )
    street_address = models.TextField(blank=True, verbose_name=_("Address"))
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name=_("Credit Limit"),
        help_text=_('Maximum credit allowed')
    )
    payment_terms_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Payment Terms (Days)"),
        help_text=_('Days until payment due after delivery')
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
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


class CustomerPhoneNumber(models.Model):
    """Additional phone numbers for a Customer."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='additional_phones')
    phone = models.CharField(max_length=20, verbose_name=_("Phone"))
    notes = models.CharField(max_length=100, blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Customer phone number")
        verbose_name_plural = _("Customer phone numbers")

    def __str__(self):
        return f"{self.phone} ({self.customer.name})"


class Salesperson(SoftDeleteMixin):
    """Sales rep for order assignment."""
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salesperson_profile', verbose_name=_("User")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Salesperson")
        verbose_name_plural = _("Salespeople")
        ordering = ['name']

    def __str__(self):
        return self.name


class SalespersonPhoneNumber(models.Model):
    """Additional phone numbers for a Salesperson."""
    salesperson = models.ForeignKey(Salesperson, on_delete=models.CASCADE, related_name='additional_phones')
    phone = models.CharField(max_length=20, verbose_name=_("Phone"))
    notes = models.CharField(max_length=100, blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Salesperson phone number")
        verbose_name_plural = _("Salesperson phone numbers")

    def __str__(self):
        return f"{self.phone} ({self.salesperson.name})"
