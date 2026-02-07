from django.contrib import admin
from django.utils import timezone
from master_data.constants import RETURN_APPROVED, RETURN_COMPLETED
from .models import ReturnRequest, ReturnItem, ReturnProcessing


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'order', 'status', 'return_type', 'total_amount', 'created_at']
    list_filter = ['status', 'return_type', 'created_at']
    search_fields = ['return_number', 'order__order_number']
    date_hierarchy = 'created_at'
    inlines = [ReturnItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    def delete_queryset(self, request, queryset):
        """Soft delete: set deleted_at instead of hard delete. Skip APPROVED/COMPLETED."""
        to_soft_delete = queryset.exclude(status__code__in=(RETURN_APPROVED, RETURN_COMPLETED))
        count, _ = to_soft_delete.update(deleted_at=timezone.now())
        skipped = queryset.count() - count
        if skipped > 0:
            from django.contrib import messages
            messages.warning(
                request,
                f'{skipped} approved/completed return(s) were not deleted (affect stock).'
            )


@admin.register(ReturnProcessing)
class ReturnProcessingAdmin(admin.ModelAdmin):
    list_display = ['return_request', 'action', 'processed_by', 'processed_at']
