from django.contrib import admin
from .models import Product, ProductVariant, ProductPriceTier, Batch, StockMovement


class ProductPriceTierInline(admin.TabularInline):
    model = ProductPriceTier
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'stock_quantity', 'base_price', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'sku']
    inlines = [ProductPriceTierInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'stock_quantity', 'price_adjustment']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['product', 'batch_number', 'quantity', 'expiry_date']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reference_type', 'created_at']
