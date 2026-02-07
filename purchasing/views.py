from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator
from core.models import Product
from master_data.models import Supplier

from .models import PurchaseOrder
from .forms import PurchaseOrderCreateForm, PurchaseReceiveItemForm
from .services import receive_purchase_items, create_purchase_order, parse_purchase_items_from_post
from django.forms import formset_factory


@login_required
def purchase_order_list(request):
    """List all purchase orders"""
    status_filter = request.GET.get('status', '')
    
    orders = PurchaseOrder.objects.filter(
        deleted_at__isnull=True
    ).select_related('supplier')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': _('Purchase Orders'),
        'orders': page_obj,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'status_filter': status_filter,
    }
    return render(request, 'purchasing/list.html', context)


@login_required
@permission_required('purchasing.add_purchaseorder', raise_exception=True)
def purchase_order_create(request):
    """Create new purchase order - delegates to service layer."""
    form = PurchaseOrderCreateForm(
        data=request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        items, parse_error = parse_purchase_items_from_post(request.POST)
        if parse_error:
            messages.error(request, parse_error)
            return redirect('purchasing:purchase_order_create')

        try:
            po = create_purchase_order(
                supplier_id=form.cleaned_data['supplier'].id,
                expected_date=form.cleaned_data.get('expected_date'),
                notes=form.cleaned_data.get('notes') or '',
                items=items,
                user=request.user,
            )
            messages.success(request, _('Purchase Order #%(id)s created successfully') % {'id': po.id})
            return redirect('purchasing:purchase_order_detail', pk=po.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('purchasing:purchase_order_create')

    context = {
        'title': _('Create Purchase Order'),
        'form': form,
        'products': Product.objects.filter(is_active=True).select_related('category'),
    }
    return render(request, 'purchasing/create.html', context)


@login_required
def purchase_order_detail(request, pk):
    """View purchase order details"""
    po = get_object_or_404(
        PurchaseOrder.objects.filter(deleted_at__isnull=True).select_related(
            'supplier', 'created_by'
        ),
        pk=pk
    )
    items = po.items.select_related('product').all()
    
    context = {
        'title': _('Purchase Order #%(id)s') % {'id': po.id},
        'po': po,
        'items': items,
    }
    return render(request, 'purchasing/detail.html', context)


@login_required
@permission_required('purchasing.delete_purchaseorder', raise_exception=True)
def purchase_order_delete(request, pk):
    """Soft delete purchase order - only if not RECEIVED."""
    po = get_object_or_404(
        PurchaseOrder.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    if request.method == 'POST':
        if po.status == 'RECEIVED':
            messages.error(
                request,
                _('Cannot delete received purchase orders. Stock was already added.')
            )
            return redirect('purchasing:purchase_order_detail', pk=pk)

        with transaction.atomic():
            po.deleted_at = timezone.now()
            po.save()
        messages.success(request, _('Purchase order deleted successfully.'))
        return redirect('purchasing:purchase_order_list')

    context = {
        'title': _('Delete Purchase Order'),
        'po': po,
    }
    return render(request, 'purchasing/po_confirm_delete.html', context)


@login_required
@permission_required('purchasing.change_purchaseorder', raise_exception=True)
def purchase_order_receive(request, pk):
    """Mark items as received and update stock using formset."""
    po = get_object_or_404(
        PurchaseOrder.objects.filter(deleted_at__isnull=True), pk=pk
    )
    items = list(po.items.select_related('product').all())
    for item in items:
        item.remaining_to_receive = item.quantity - item.received_quantity

    ReceiveFormSet = formset_factory(
        PurchaseReceiveItemForm,
        extra=0,
        max_num=len(items),
        validate_max=True,
    )
    initial = [
        {'item_id': item.id, 'received_quantity': 0}
        for item in items
    ]

    if request.method == 'POST':
        formset = ReceiveFormSet(
            data=request.POST,
            initial=initial,
        )
        if formset.is_valid():
            received_data = []
            for form in formset:
                item_id = form.cleaned_data['item_id']
                qty = form.cleaned_data['received_quantity']
                expiry_date = form.cleaned_data.get('expiry_date')
                if qty > 0:
                    received_data.append({
                        'item_id': item_id,
                        'quantity': qty,
                        'expiry_date': expiry_date
                    })
            try:
                receive_purchase_items(po, received_data, user=request.user)
                messages.success(request, _('Stock updated successfully'))
            except ValueError as e:
                messages.error(request, str(e))
            return redirect('purchasing:purchase_order_detail', pk=po.id)
    else:
        formset = ReceiveFormSet(initial=initial)

    formset_with_items = list(zip(formset, items))
    context = {
        'title': _('Receive PO #%(id)s') % {'id': po.id},
        'po': po,
        'items': items,
        'formset': formset,
        'formset_with_items': formset_with_items,
    }
    return render(request, 'purchasing/receive.html', context)
