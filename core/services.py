"""
Stock services - deduct, restore, adjust.
"""
from django.db import transaction
from django.db.models import F

from core.models import Batch, Product, StockMovement


def deduct_stock(product_id, quantity, reference_type, reference_id, batch_id=None, user=None):
    """Create OUT movement, update Product.stock_quantity."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        if product.stock_quantity < quantity:
            raise ValueError(f"Insufficient stock for {product.name}. Available: {product.stock_quantity}")
        product.stock_quantity -= quantity
        product.save()
        if batch_id:
            batch = Batch.objects.select_for_update().get(id=batch_id)
            if batch.quantity < quantity:
                raise ValueError(f"Insufficient batch stock for {product.name} ({batch.batch_number}). Available: {batch.quantity}")
            batch.quantity -= quantity
            batch.save()
        StockMovement.objects.create(
            product=product,
            batch_id=batch_id,
            movement_type='OUT',
            quantity=-quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=user,
        )
    return product


def restore_stock(product_id, quantity, reference_type, reference_id, batch_id=None, user=None):
    """Create RETURN movement, update Product.stock_quantity."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity
        product.save()
        if batch_id:
            batch = Batch.objects.select_for_update().get(id=batch_id)
            batch.quantity += quantity
            batch.save()
        StockMovement.objects.create(
            product=product,
            batch_id=batch_id,
            movement_type='RETURN',
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=user,
        )
    return product


def adjust_stock(product_id, quantity, reason, approved_by):
    """Manual adjustment with ADJUST movement type."""
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity
        product.save()
        StockMovement.objects.create(
            product=product,
            movement_type='ADJUST',
            quantity=quantity,
            reference_type='ADJUST',
            notes=reason,
            created_by=approved_by,
        )
    return product


def add_stock(product_id, quantity, reference_type, reference_id, notes='', user=None):
    """
    Add stock (IN movement). Use for purchase receive, batch create, etc.
    Never update Product.stock_quantity directly - always use this service.
    """
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity
        product.save()
        StockMovement.objects.create(
            product=product,
            movement_type='IN',
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes or '',
            created_by=user,
        )
    return product


def add_stock_from_batch(product_id, quantity, batch_id, reference_id, user=None):
    """Add stock from batch creation. Delegates to add_stock."""
    return add_stock(
        product_id=product_id,
        quantity=quantity,
        reference_type='Batch',
        reference_id=reference_id,
        user=user,
    )


def adjust_stock_from_batch(product_id, quantity_delta, batch_id, reference_id, user=None):
    """
    Adjust stock when batch quantity changes. Uses service layer.
    Creates StockMovement ADJUST and updates Product.stock_quantity.
    """
    if quantity_delta == 0:
        return Product.objects.get(id=product_id)
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity_delta
        product.save()
        StockMovement.objects.create(
            product=product,
            batch_id=batch_id,
            movement_type='ADJUST',
            quantity=quantity_delta,
            reference_type='Batch',
            reference_id=reference_id,
            notes='Batch quantity update',
            created_by=user,
        )
    return product


def check_low_stock():
    """Return products below threshold for alerts."""
    return Product.objects.filter(
        is_active=True,
        stock_quantity__lte=F('low_stock_threshold')
    )
