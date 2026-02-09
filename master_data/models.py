"""
Master Data models - configurable lookup tables.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _, get_language

from common.models import SoftDeleteMixin


class BaseMasterModel(SoftDeleteMixin):
    """Base for master data models with bilingual support."""
    code = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=200)
    name_my = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_display_name(self, lang='en'):
        """Return name_en or name_my based on language."""
        if lang == 'my' and self.name_my:
            return self.name_my
        return self.name_en

    @property
    def name(self):
        """Dynamic name based on current language."""
        return self.get_display_name(get_language())

    def __str__(self):
        return self.name


class CustomerType(BaseMasterModel):
    """Individual, Shop, Distributor"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Customer type")
        verbose_name_plural = _("Customer types")
        ordering = ['sort_order', 'code']


class ReturnReason(BaseMasterModel):
    """Expired, Damaged, Wrong Quantity, Quality Issues, Other"""
    requires_notes = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Return reason")
        verbose_name_plural = _("Return reasons")
        ordering = ['code']


class ReturnType(BaseMasterModel):
    """Refund, Replacement, Exchange, Credit Note"""
    class Meta:
        verbose_name = _("Return type")
        verbose_name_plural = _("Return types")
        ordering = ['code']


class PaymentMethod(BaseMasterModel):
    """Cash, Bank Transfer, Mobile Banking, Check, Credit, Mobile Money, Other"""
    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ['code']


class OrderStatus(BaseMasterModel):
    """Pending, Confirmed, Delivered, Paid, Cancelled"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Order status")
        verbose_name_plural = _("Order statuses")
        ordering = ['sort_order', 'code']

    @classmethod
    def get_by_code(cls, code):
        """Get status by code. Raises OrderStatus.DoesNotExist if not found."""
        return cls.objects.get(code=code)


class ReturnRequestStatus(BaseMasterModel):
    """Pending, Approved, Rejected, Completed"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Return request status")
        verbose_name_plural = _("Return request statuses")
        ordering = ['sort_order', 'code']

    @classmethod
    def get_by_code(cls, code):
        """Get status by code. Raises ReturnRequestStatus.DoesNotExist if not found."""
        return cls.objects.get(code=code)


class ProductCategory(BaseMasterModel):
    """Product grouping for filter/report"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Product category")
        verbose_name_plural = _("Product categories")
        ordering = ['sort_order', 'code']


class UnitOfMeasure(BaseMasterModel):
    """ပဲခွဲ, ဘူး, ဘူးအစု, ကာတန်, etc."""
    class Meta:
        verbose_name = _("Unit of measure")
        verbose_name_plural = _("Units of measure")
        ordering = ['code']


class TaxRate(BaseMasterModel):
    """Commercial tax / VAT (Myanmar compliance)"""
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Tax rate")
        verbose_name_plural = _("Tax rates")
        ordering = ['code']


class ContactType(BaseMasterModel):
    """Phone, Visit, Email, Meeting, Other - for CRM contact logs"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Contact type")
        verbose_name_plural = _("Contact types")
        ordering = ['sort_order', 'code']


class Country(BaseMasterModel):
    """Country"""
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ['sort_order', 'code']


class Region(BaseMasterModel):
    """State/Division"""
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, related_name='regions',
        null=True, blank=True, verbose_name=_("Country")
    )

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        ordering = ['code']


class DeliveryRoute(BaseMasterModel):
    """Route for delivery optimization"""
    class Meta:
        verbose_name = _("Delivery route")
        verbose_name_plural = _("Delivery routes")
        ordering = ['code']


class Township(BaseMasterModel):
    """Township linked to Region"""
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='townships')
    delivery_route = models.ForeignKey(
        DeliveryRoute, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='townships'
    )
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Township")
        verbose_name_plural = _("Townships")
        ordering = ['region', 'name_en']


class Supplier(BaseMasterModel):
    """Product suppliers"""
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['name_en']


class Promotion(BaseMasterModel):
    """Simple promotion rules"""
    start_date = models.DateField()
    end_date = models.DateField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ['-end_date']
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]


class Currency(BaseMasterModel):
    """Base currency - affects whole system (invoices, reports, etc.)"""
    symbol = models.CharField(max_length=10, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ['sort_order', 'code']


class CompanySetting(models.Model):
    """Singleton for company info"""
    class Meta:
        verbose_name = _("Company setting")
        verbose_name_plural = _("Company settings")

    name = models.CharField(max_length=200, default='My Company')
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    footer_text = models.TextField(blank=True, help_text="Text for invoice footer")
    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='company_settings'
    )
    township = models.ForeignKey(
        Township, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='company_settings'
    )
    base_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, null=True, blank=True,
        related_name='company_settings'
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and CompanySetting.objects.exists():
            # If you want to ensure only one object, you can raise an error or delete old one
            pass # Simplified for now
        super().save(*args, **kwargs)
