from django.contrib import admin
from .models import (
    CustomerType, ReturnReason, ReturnType, PaymentMethod,
    OrderStatus, ReturnRequestStatus, ProductCategory, UnitOfMeasure, TaxRate,
    ContactType, Region, Township, DeliveryRoute, Supplier, Promotion,
    Currency, CompanySetting
)


@admin.register(CustomerType, ReturnReason, ReturnType, PaymentMethod,
                OrderStatus, ReturnRequestStatus, ProductCategory, UnitOfMeasure, TaxRate,
                ContactType, Region, DeliveryRoute, Supplier, Currency)
class MasterDataAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_en', 'name_my', 'is_active']
    list_filter = ['is_active']

@admin.register(Township)
class TownshipAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_en', 'region', 'delivery_route', 'delivery_fee']
    list_filter = ['region', 'delivery_route']

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_en', 'start_date', 'end_date', 'discount_percent']
    list_filter = ['start_date', 'end_date']

@admin.register(CompanySetting)
class CompanySettingAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'township', 'base_currency', 'phone', 'email']

    def get_readonly_fields(self, request, obj=None):
        from .utils import has_transactional_data
        readonly = list(super().get_readonly_fields(request, obj))
        if has_transactional_data():
            readonly.append('base_currency')
        return readonly

    def has_add_permission(self, request):
        # Only allow one setting object
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
