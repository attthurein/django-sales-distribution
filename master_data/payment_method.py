"""
Payment Method master data model.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.Model):
    """Payment methods for transactions."""
    code = models.CharField(_("Code"), max_length=50, unique=True)
    name_en = models.CharField(_("Name (English)"), max_length=100)
    name_my = models.CharField(_("Name (Myanmar)"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ['display_order', 'name_en']
    
    def __str__(self):
        return self.name_en
