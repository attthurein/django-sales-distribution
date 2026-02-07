from django.contrib import admin
from .models import Customer, Salesperson


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop_name', 'contact_person', 'phone', 'customer_type', 'salesperson', 'credit_limit', 'payment_terms_days', 'is_active', 'created_at']
    list_filter = ['customer_type', 'is_active']
    search_fields = ['name', 'shop_name', 'contact_person', 'phone', 'street_address']
    date_hierarchy = 'created_at'


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'user', 'is_active']
