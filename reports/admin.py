from django.contrib import admin
from .models import DailySalesSummary, DailyInventorySnapshot, DailyPaymentSummary, DailyExpenseSummary

@admin.register(DailySalesSummary)
class DailySalesSummaryAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_revenue', 'total_orders', 'total_items_sold', 'gross_profit')
    list_filter = ('date',)
    date_hierarchy = 'date'

@admin.register(DailyPaymentSummary)
class DailyPaymentSummaryAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_collected', 'transaction_count')
    date_hierarchy = 'date'

@admin.register(DailyExpenseSummary)
class DailyExpenseSummaryAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_expense', 'transaction_count')
    date_hierarchy = 'date'

@admin.register(DailyInventorySnapshot)
class DailyInventorySnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'product', 'quantity_on_hand', 'total_value')
    list_filter = ('date', 'product__category')
    search_fields = ('product__name', 'product__sku')
    date_hierarchy = 'date'
