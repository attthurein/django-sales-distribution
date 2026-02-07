from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from common.models import SoftDeleteMixin


class ExpenseCategory(models.Model):
    """Category for expenses (e.g. Logistics, Salary)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Expense category")
        verbose_name_plural = _("Expense categories")
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(SoftDeleteMixin):
    """Company expenses"""
    date = models.DateField()
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    paid_to = models.CharField(max_length=200, blank=True)
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='recorded_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"
