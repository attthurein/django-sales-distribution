from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Product

class DailySalesSummary(models.Model):
    """Summary of sales for a specific day."""
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_items_sold = models.PositiveIntegerField(default=0)
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Daily Sales Summary")
        verbose_name_plural = _("Daily Sales Summaries")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Sales Summary: {self.date}"

class DailyInventorySnapshot(models.Model):
    """Snapshot of inventory levels at the end of a specific day."""
    date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_snapshots')
    quantity_on_hand = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # qty * cost_price (or base_price)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Daily Inventory Snapshot")
        verbose_name_plural = _("Daily Inventory Snapshots")
        ordering = ['-date', 'product']
        unique_together = ['date', 'product']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"Inventory: {self.product.name} on {self.date}"

class DailyPaymentSummary(models.Model):
    """Summary of payments collected for a specific day."""
    date = models.DateField(unique=True)
    total_collected = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    # Could expand to JSON field for breakdown by method if DB supports it, 
    # but for simple SQL compliance, we stick to totals or separate rows.
    # We will keep it simple: Total collected.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Daily Payment Summary")
        verbose_name_plural = _("Daily Payment Summaries")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Payment Summary: {self.date}"

class DailyExpenseSummary(models.Model):
    """Summary of expenses for a specific day."""
    date = models.DateField(unique=True)
    total_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Daily Expense Summary")
        verbose_name_plural = _("Daily Expense Summaries")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Expense Summary: {self.date}"
