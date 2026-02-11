from django.contrib import admin
from django.utils import timezone
from .models import Lead, LeadPhoneNumber, ContactLog, SampleDelivery


class LeadPhoneNumberInline(admin.TabularInline):
    model = LeadPhoneNumber
    extra = 1


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop_name', 'contact_person', 'phone', 'township', 'status', 'source', 'assigned_to', 'created_at']
    list_filter = ['status', 'township__region']
    search_fields = ['name', 'shop_name', 'contact_person', 'phone']
    inlines = [LeadPhoneNumberInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    def delete_queryset(self, request, queryset):
        """Soft delete: set deleted_at instead of hard delete."""
        queryset.update(deleted_at=timezone.now())


@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ['lead', 'customer', 'contact_type', 'next_follow_up', 'created_at']


@admin.register(SampleDelivery)
class SampleDeliveryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'status', 'lead', 'customer', 'given_at', 'is_deleted']
    list_filter = ['status', 'given_at', 'deleted_at']
    search_fields = ['product__name', 'lead__name', 'customer__name']
    actions = ['soft_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        """Show only active (non-deleted) records by default."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    def delete_queryset(self, request, queryset):
        """Soft delete: set deleted_at instead of hard delete."""
        queryset.update(deleted_at=timezone.now())

    def is_deleted(self, obj):
        """Show if record is soft deleted."""
        return obj.is_deleted
    is_deleted.boolean = True
    is_deleted.short_description = 'Deleted'

    def soft_delete_selected(self, request, queryset):
        """Admin action to soft delete selected records."""
        count = queryset.count()
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{count} sample deliveries were soft deleted.')
    soft_delete_selected.short_description = 'Soft delete selected sample deliveries'

    def restore_selected(self, request, queryset):
        """Admin action to restore soft deleted records."""
        count = queryset.count()
        for obj in queryset:
            obj.restore()
        self.message_user(request, f'{count} sample deliveries were restored.')
    restore_selected.short_description = 'Restore selected sample deliveries'
