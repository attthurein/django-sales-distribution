"""
Product & Inventory views.
"""
from django.db.models import Count, Q, Prefetch
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from .models import Batch, Product, ProductPriceTier, StockMovement
from .forms import ProductForm, StockAdjustmentForm
from .services import check_low_stock, adjust_stock
from master_data.models import CustomerType, ProductCategory, UnitOfMeasure
from common.constants import PAGE_SIZE_PRODUCTS, LIMIT_STOCK_MOVEMENTS


@login_required
@permission_required('core.add_product', raise_exception=True)
def product_create(request):
    """Create product with price tiers."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect('core:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
@permission_required('core.change_product', raise_exception=True)
def product_edit(request, pk):
    """Edit product with price tiers."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('core:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@login_required
@permission_required('core.view_product', raise_exception=True)
def product_list(request):
    """List products."""
    products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'unit').annotate(
        expiry_count=Count('batches__expiry_date', filter=Q(batches__quantity__gt=0), distinct=True)
    ).prefetch_related(
        Prefetch('batches', queryset=Batch.objects.filter(quantity__gt=0).order_by('expiry_date'), to_attr='active_batches')
    ).order_by('name')
    paginator = Paginator(products, PAGE_SIZE_PRODUCTS)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    return render(request, 'core/product_list.html', {'products': products})


@login_required
@permission_required('core.view_product', raise_exception=True)
def product_detail(request, pk):
    """Product detail with stock movements."""
    product = get_object_or_404(
        Product.objects.prefetch_related('price_tiers__customer_type'),
        pk=pk
    )
    movements = product.stock_movements.select_related('created_by').order_by('-created_at')[:LIMIT_STOCK_MOVEMENTS]
    return render(request, 'core/product_detail.html', {
        'product': product,
        'movements': movements,
    })


@login_required
@permission_required('core.view_stockmovement', raise_exception=True)
def stock_movement_list(request):
    """Stock movement history."""
    movements = StockMovement.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')[:100]
    return render(request, 'core/stock_movement_list.html', {'movements': movements})


@login_required
@permission_required('core.view_product', raise_exception=True)
def low_stock_list(request):
    """Low stock alerts."""
    products = check_low_stock().select_related('category').order_by('stock_quantity')
    return render(request, 'core/low_stock_list.html', {'products': products})


@login_required
@permission_required('core.change_product', raise_exception=True)
def stock_adjust(request, pk):
    """Manual stock adjustment. Uses core.services.adjust_stock."""
    product = get_object_or_404(Product, pk=pk)
    form = StockAdjustmentForm(
        data=request.POST if request.method == 'POST' else None,
        product=product,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']
            expiry_date = form.cleaned_data.get('expiry_date')

            if expiry_date:
                # Batch adjustment
                batch = Batch.objects.filter(product=product, expiry_date=expiry_date).first()
                if not batch:
                    if quantity < 0:
                        raise ValueError(_("Cannot deduct from non-existent batch (Expiry: %(date)s)") % {'date': expiry_date})
                    # Create new batch
                    batch = Batch(
                        product=product,
                        batch_number=f"BATCH-{expiry_date.strftime('%Y%m%d')}",
                        quantity=0, # Will be added below
                        expiry_date=expiry_date,
                        notes=reason
                    )
                    batch.save() # Initial save (qty 0)
                
                # Update batch quantity (triggers Product update via Batch.save logic)
                batch.quantity += quantity
                batch.save()
                
                msg = _('Batch adjusted: %(product)s (%(date)s) by %(qty)+d. New batch stock: %(new)s') % {
                    'product': product.name,
                    'date': expiry_date,
                    'qty': quantity,
                    'new': batch.quantity,
                }
            else:
                # Global adjustment
                adjust_stock(
                    product_id=product.id,
                    quantity=quantity,
                    reason=reason,
                    approved_by=request.user,
                )
                msg = _('Stock adjusted: %(product)s by %(qty)+d. New stock: %(new)s') % {
                    'product': product.name,
                    'qty': quantity,
                    'new': product.stock_quantity + quantity,
                }
            
            messages.success(request, msg)
            return redirect('core:product_detail', pk=product.pk)
        except ValueError as e:
            messages.error(request, str(e))
    context = {
        'form': form,
        'product': product,
        'title': _('Adjust Stock'),
    }
    return render(request, 'core/stock_adjust.html', context)


@login_required
@permission_required('core.view_product', raise_exception=True)
def batches_for_product(request, product_id):
    """AJAX endpoint: return batches for a product (id, batch_number, quantity, expiry_date)."""
    qs = Product.objects.filter(pk=product_id, is_active=True)
    if not qs.exists():
        return JsonResponse({'success': False, 'batches': []})
    batches = Batch.objects.filter(product_id=product_id).order_by('-created_at')
    data = []
    for b in batches:
        data.append({
            'id': b.id,
            'batch_number': b.batch_number,
            'quantity': b.quantity,
            'expiry_date': b.expiry_date.isoformat() if b.expiry_date else '',
        })
    return JsonResponse({'success': True, 'batches': data})
