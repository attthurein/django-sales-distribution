from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import Customer, Salesperson
from .forms import CustomerForm, SalespersonForm
from master_data.models import CustomerType
from orders.models import SalesOrder
from crm.models import SampleDelivery
from common.utils import get_regions_with_townships
from common.constants import PAGE_SIZE_CUSTOMERS, LIMIT_CUSTOMER_SEARCH, LIMIT_RECENT_ORDERS


@login_required
def customer_list(request):
    """List all customers with search functionality"""
    search_query = request.GET.get('q', '')
    customer_type = request.GET.get('customer_type', '')

    customers = Customer.objects.filter(
        deleted_at__isnull=True, is_active=True
    ).select_related('customer_type', 'township')

    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    if customer_type:
        customers = customers.filter(customer_type_id=customer_type)

    customers = customers.order_by('name')
    paginator = Paginator(customers, PAGE_SIZE_CUSTOMERS)
    page = request.GET.get('page', 1)
    customers = paginator.get_page(page)

    context = {
        'title': _('Customers'),
        'customers': customers,
        'search_query': search_query,
        'customer_type': customer_type,
        'customer_types': CustomerType.objects.all(),
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_detail(request, pk):
    """View customer details"""
    customer = get_object_or_404(
        Customer.objects.filter(deleted_at__isnull=True).select_related('customer_type', 'township'),
        pk=pk
    )
    recent_orders = SalesOrder.objects.filter(
        customer=customer, deleted_at__isnull=True
    ).select_related('status').order_by('-created_at')[:LIMIT_RECENT_ORDERS]
    sample_deliveries = SampleDelivery.objects.filter(customer=customer).select_related('product').order_by('-given_at')

    context = {
        'title': _('Customer Detail'),
        'customer': customer,
        'recent_orders': recent_orders,
        'sample_deliveries': sample_deliveries,
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
@permission_required('customers.add_customer', raise_exception=True)
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, _('Customer created successfully.'))
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    regions = get_regions_with_townships()
    context = {
        'title': _('Add New Customer'),
        'form': form,
        'regions': regions,
        'customer': None,
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@permission_required('customers.change_customer', raise_exception=True)
def customer_update(request, pk):
    """Update customer"""
    customer = get_object_or_404(Customer.objects.filter(deleted_at__isnull=True), pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _('Customer updated successfully.'))
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    regions = get_regions_with_townships()
    context = {
        'title': _('Edit Customer'),
        'form': form,
        'customer': customer,
        'regions': regions,
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@permission_required('customers.delete_customer', raise_exception=True)
def customer_delete(request, pk):
    """Soft delete customer - sets deleted_at and is_active=False."""
    customer = get_object_or_404(Customer.objects.filter(deleted_at__isnull=True), pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            customer.deleted_at = timezone.now()
            customer.is_active = False
            customer.save()
        messages.success(request, _('Customer deleted successfully.'))
        return redirect('customers:customer_list')

    context = {
        'title': _('Delete Customer'),
        'customer': customer,
    }
    return render(request, 'customers/delete.html', context)


@login_required
def customer_search_ajax(request):
    """AJAX endpoint for customer search"""
    query = request.GET.get('q', '')

    if len(query) < 3:
        return JsonResponse({'customers': []})

    customers = Customer.objects.filter(
        deleted_at__isnull=True,
        is_active=True,
    ).filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query)
    ).select_related('customer_type')[:LIMIT_CUSTOMER_SEARCH]

    customer_data = [
        {
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'customer_type': (
                c.customer_type.name_my if c.customer_type and c.customer_type.name_my
                else (c.customer_type.name_en if c.customer_type else '')
            ),
            'display_name': c.name,
        }
        for c in customers
    ]

    return JsonResponse({'customers': customer_data})


@login_required
def salesperson_list(request):
    """List salespeople."""
    salespeople = Salesperson.objects.filter(deleted_at__isnull=True).order_by('name')
    return render(request, 'customers/salesperson_list.html', {
        'salespeople': salespeople,
        'title': _('Salespeople')
    })


@login_required
@permission_required('customers.add_salesperson', raise_exception=True)
def salesperson_create(request):
    """Create salesperson."""
    if request.method == 'POST':
        form = SalespersonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Salesperson created.'))
            return redirect('customers:salesperson_list')
    else:
        form = SalespersonForm()
    return render(request, 'customers/salesperson_form.html', {
        'form': form,
        'title': _('Add Salesperson')
    })


@login_required
@permission_required('customers.change_salesperson', raise_exception=True)
def salesperson_edit(request, pk):
    """Edit salesperson."""
    salesperson = get_object_or_404(Salesperson.objects.filter(deleted_at__isnull=True), pk=pk)
    if request.method == 'POST':
        form = SalespersonForm(request.POST, instance=salesperson)
        if form.is_valid():
            form.save()
            messages.success(request, _('Salesperson updated.'))
            return redirect('customers:salesperson_list')
    else:
        form = SalespersonForm(instance=salesperson)
    return render(request, 'customers/salesperson_form.html', {
        'form': form,
        'title': _('Edit Salesperson')
    })
