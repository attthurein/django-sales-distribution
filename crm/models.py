"""
CRM models - Lead, ContactLog, SampleDelivery.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from customers.models import Customer
from core.models import Product
from common.models import SoftDeleteMixin
from master_data.models import ContactType


class Lead(SoftDeleteMixin):
    """Lead/Prospect before conversion to Customer."""
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('SAMPLE_GIVEN', 'Sample Given'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
    ]
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
    address = models.TextField(blank=True)
    township = models.ForeignKey(
        'master_data.Township', on_delete=models.PROTECT, null=True, blank=True,
        related_name='leads', help_text='Location township (links to Region)'
    )
    source = models.CharField(max_length=100, blank=True, help_text='Where the lead came from')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='leads_converted', help_text='Set when converted to customer'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Lead")
        verbose_name_plural = _("Leads")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class LeadPhoneNumber(models.Model):
    """Additional phone numbers for a Lead."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='additional_phones')
    phone = models.CharField(max_length=20, verbose_name=_("Phone"))
    notes = models.CharField(max_length=100, blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Lead phone number")
        verbose_name_plural = _("Lead phone numbers")

    def __str__(self):
        return f"{self.phone} ({self.lead.name})"


class ContactLog(SoftDeleteMixin):
    """Phone call, visit, or other contact with lead/customer."""
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, null=True, blank=True,
        related_name='contact_logs'
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True,
        related_name='contact_logs'
    )
    contact_type = models.ForeignKey(
        ContactType, on_delete=models.PROTECT, related_name='contact_logs',
        help_text='Type of contact (from Master Data)'
    )
    notes = models.TextField(help_text='Contact summary')
    next_follow_up = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Contact log")
        verbose_name_plural = _("Contact logs")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contact_type} - {self.created_at}"


class SampleDelivery(SoftDeleteMixin):
    """Sample given to lead/customer."""
    STATUS_CHOICES = [
        ('GIVEN', 'Given'),
        ('RETURNED', 'Returned'),
        ('NOT_RETURNED', 'Not Returned'),
        ('CONVERTED', 'Converted to Sale'),
    ]
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, null=True, blank=True,
        related_name='sample_deliveries'
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True,
        related_name='sample_deliveries'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sample_deliveries')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GIVEN')
    given_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Sample delivery")
        verbose_name_plural = _("Sample deliveries")
        ordering = ['-given_at']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} - {self.status}"
