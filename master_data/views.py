"""
Master Data views.
"""
from django.contrib.auth.decorators import login_required, permission_required
from common.utils import get_countries_with_regions
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator

from .models import CompanySetting, Supplier
from .forms import CompanySettingForm, SupplierForm, SupplierPhoneNumberFormSet
from .utils import has_transactional_data


@login_required
@permission_required('master_data.change_companysetting', raise_exception=True)
def company_setting(request):
    """View and edit company settings (singleton)."""
    instance = CompanySetting.objects.first()
    countries = get_countries_with_regions()

    if request.method == 'POST':
        form = CompanySettingForm(
            request.POST, request.FILES, instance=instance,
            base_currency_locked=has_transactional_data(),
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, _('Company settings saved successfully.')
            )
            return redirect('master_data:company_setting')
    else:
        form = CompanySettingForm(
            instance=instance,
            base_currency_locked=has_transactional_data(),
        )

    return render(request, 'master_data/company_setting_form.html', {
        'form': form,
        'setting': instance,
        'countries': countries,
        'base_currency_locked': has_transactional_data(),
    })


@login_required
@permission_required('master_data.view_supplier', raise_exception=True)
def supplier_list(request):
    """List suppliers."""
    suppliers_list = Supplier.objects.filter(is_active=True).prefetch_related('additional_phones').order_by('name_en')
    
    paginator = Paginator(suppliers_list, 20)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)
    
    return render(request, 'master_data/supplier_list.html', {
        'suppliers': suppliers,
        'title': _('Suppliers')
    })


@login_required
@permission_required('master_data.add_supplier', raise_exception=True)
def supplier_create(request):
    """Create supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        formset = SupplierPhoneNumberFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                supplier = form.save()
                formset.instance = supplier
                formset.save()
            messages.success(request, _('Supplier created successfully.'))
            return redirect('master_data:supplier_list')
    else:
        form = SupplierForm()
        formset = SupplierPhoneNumberFormSet()
    
    return render(request, 'master_data/supplier_form.html', {
        'title': _('Add Supplier'),
        'form': form,
        'formset': formset,
    })


@login_required
@permission_required('master_data.view_supplier', raise_exception=True)
def supplier_detail(request, pk):
    """Supplier detail."""
    supplier = get_object_or_404(Supplier, pk=pk)
    return render(request, 'master_data/supplier_detail.html', {
        'supplier': supplier,
        'title': supplier.name_en
    })


@login_required
@permission_required('master_data.change_supplier', raise_exception=True)
def supplier_update(request, pk):
    """Update supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        formset = SupplierPhoneNumberFormSet(request.POST, instance=supplier)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, _('Supplier updated successfully.'))
            return redirect('master_data:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
        formset = SupplierPhoneNumberFormSet(instance=supplier)
    
    return render(request, 'master_data/supplier_form.html', {
        'title': _('Edit Supplier'),
        'form': form,
        'formset': formset,
        'supplier': supplier
    })


@login_required
@permission_required('master_data.delete_supplier', raise_exception=True)
def supplier_delete(request, pk):
    """Soft delete supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.is_active = False
        supplier.save()
        messages.success(request, _('Supplier deleted successfully.'))
    return redirect('master_data:supplier_list')
