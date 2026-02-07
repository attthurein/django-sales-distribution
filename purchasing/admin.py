from django.contrib import admin
from django.utils import timezone
from .models import PurchaseOrder, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'date_ordered', 'total_amount', 'status']
    list_filter = ['status', 'order_date']
    inlines = [PurchaseItemInline]

    def date_ordered(self, obj):
        return obj.order_date

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    def delete_queryset(self, request, queryset):
        """Soft delete: set deleted_at instead of hard delete. Skip RECEIVED."""
        to_soft_delete = queryset.exclude(status='RECEIVED')
        count, _ = to_soft_delete.update(deleted_at=timezone.now())
        skipped = queryset.count() - count
        if skipped > 0:
            from django.contrib import messages
            messages.warning(
                request,
                f'{skipped} received purchase order(s) were not deleted (stock already added).'
            )

