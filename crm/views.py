"""CRM views - Lead, ContactLog, SampleDelivery."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .models import Lead, ContactLog, SampleDelivery
from .forms import LeadForm, ContactLogForm, SampleDeliveryForm, LeadConvertForm
from customers.models import Customer
from core.models import Product
from master_data.models import ContactType, CustomerType
from master_data.constants import (
    LEAD_STATUS_NEW,
    LEAD_STATUS_CONTACTED,
    LEAD_STATUS_CONVERTED,
    SAMPLE_STATUS_GIVEN,
    SAMPLE_STATUS_RETURNED,
    SAMPLE_STATUS_NOT_RETURNED,
)
from common.utils import get_regions_with_townships
from core.services import restore_stock
from .services import give_sample_to_lead, give_sample_to_customer, convert_lead_to_customer


@login_required
def lead_list(request):
    """List leads with status filter."""
    status_filter = request.GET.get('status', '')
    leads_list = Lead.objects.filter(
        deleted_at__isnull=True
    ).select_related('township', 'township__region').order_by('-created_at')
    if status_filter:
        leads_list = leads_list.filter(status=status_filter)

    paginator = Paginator(leads_list, 20)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)

    return render(request, 'crm/lead_list.html', {
        'leads': leads,
        'status_filter': status_filter,
    })


@login_required
def lead_detail(request, pk):
    """Lead detail with contact logs and samples."""
    lead = get_object_or_404(
        Lead.objects.filter(deleted_at__isnull=True)
        .select_related('township', 'township__region')
        .prefetch_related('contact_logs__contact_type', 'sample_deliveries__product'),
        pk=pk
    )
    return render(request, 'crm/lead_detail.html', {'lead': lead})


@login_required
@permission_required('crm.add_lead', raise_exception=True)
def lead_create(request):
    """Create new lead using ModelForm."""
    form = LeadForm(data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            lead = form.save(commit=False)
            lead.status = LEAD_STATUS_NEW
            lead.assigned_to = request.user if request.user.is_authenticated else None
            lead.save()
        messages.success(request, _('Lead created.'))
        return redirect('crm:lead_list')
    regions = get_regions_with_townships()
    return render(request, 'crm/lead_form.html', {
        'title': _('Create Lead'),
        'form': form,
        'lead': None,
        'regions': regions,
    })


@login_required
@permission_required('crm.change_lead', raise_exception=True)
def lead_edit(request, pk):
    """Edit lead using ModelForm."""
    lead = get_object_or_404(Lead.objects.filter(deleted_at__isnull=True), pk=pk)
    form = LeadForm(
        data=request.POST if request.method == 'POST' else None,
        instance=lead,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, _('Lead updated.'))
        return redirect('crm:lead_detail', pk=pk)
    regions = get_regions_with_townships()
    return render(request, 'crm/lead_form.html', {
        'lead': lead,
        'title': _('Edit Lead'),
        'form': form,
        'regions': regions,
    })


@login_required
@permission_required('crm.add_contactlog', raise_exception=True)
def contact_log_add(request, lead_id):
    """Add contact log to lead using ModelForm."""
    lead = get_object_or_404(Lead.objects.filter(deleted_at__isnull=True), pk=lead_id)
    contact_types = ContactType.objects.filter(is_active=True).order_by('sort_order', 'code')
    if not contact_types.exists():
        messages.error(
            request,
            _('No contact types found. Run: python manage.py setup_master_data')
        )
        return redirect('crm:lead_detail', pk=lead_id)

    form = ContactLogForm(
        data=request.POST if request.method == 'POST' else None,
        initial={'contact_type': contact_types.first()} if contact_types.exists() else {},
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            contact_log = form.save(commit=False)
            contact_log.lead = lead
            contact_log.created_by = request.user
            contact_log.save()
            if lead.status == LEAD_STATUS_NEW:
                lead.status = LEAD_STATUS_CONTACTED
                lead.save(update_fields=['status'])
        messages.success(request, _('Contact log added.'))
        return redirect('crm:lead_detail', pk=lead_id)
    return render(request, 'crm/contact_log_form.html', {
        'lead': lead,
        'form': form,
    })


def _sample_redirect(sample):
    """Redirect to lead or customer detail after sample action."""
    if sample.lead_id:
        return redirect('crm:lead_detail', pk=sample.lead_id)
    if sample.customer_id:
        return redirect('customers:customer_detail', pk=sample.customer_id)
    return redirect('crm:lead_list')


@login_required
@permission_required('crm.add_sampledelivery', raise_exception=True)
def sample_give(request, lead_id):
    """Give sample to lead. Deducts stock."""
    lead = get_object_or_404(Lead.objects.filter(deleted_at__isnull=True), pk=lead_id)
    form = SampleDeliveryForm(
        data=request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        product = form.cleaned_data['product']
        quantity = form.cleaned_data['quantity'] or 1
        try:
            give_sample_to_lead(lead, product, quantity, user=request.user)
            msg = _('Sample given: %(product)s x%(qty)s') % {'product': product.name, 'qty': quantity}
            messages.success(request, msg)
            return redirect('crm:lead_detail', pk=lead_id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('crm:lead_detail', pk=lead_id)
    return render(request, 'crm/sample_form.html', {'lead': lead, 'form': form})


@login_required
@permission_required('crm.change_sampledelivery', raise_exception=True)
def sample_return(request, sample_id):
    """Return sample - restore stock."""
    sample = get_object_or_404(
        SampleDelivery.objects.select_related('lead', 'customer'),
        pk=sample_id, status=SAMPLE_STATUS_GIVEN
    )
    if request.method == 'POST':
        with transaction.atomic():
            sample.status = SAMPLE_STATUS_RETURNED
            sample.returned_at = timezone.now()
            sample.save()
            restore_stock(
                product_id=sample.product_id,
                quantity=sample.quantity,
                reference_type='SampleDelivery',
                reference_id=sample.id,
                user=request.user,
            )
        messages.success(request, _('Sample returned, stock restored.'))
        return _sample_redirect(sample)
    return render(request, 'crm/sample_confirm_return.html', {'sample': sample})


@login_required
@permission_required('crm.change_sampledelivery', raise_exception=True)
def sample_mark_not_returned(request, sample_id):
    """Mark sample as not returned - customer kept it, no stock restore."""
    sample = get_object_or_404(
        SampleDelivery.objects.select_related('lead', 'customer'),
        pk=sample_id, status=SAMPLE_STATUS_GIVEN
    )
    if request.method == 'POST':
        with transaction.atomic():
            sample.status = SAMPLE_STATUS_NOT_RETURNED
            sample.returned_at = None
            sample.save()
        messages.success(request, _('Sample marked as not returned. Stock remains deducted.'))
        return _sample_redirect(sample)
    return render(request, 'crm/sample_confirm_not_returned.html', {'sample': sample})


@login_required
@permission_required('crm.add_sampledelivery', raise_exception=True)
def sample_give_for_customer(request, customer_id):
    """Give sample to customer. Deducts stock."""
    customer = get_object_or_404(Customer, pk=customer_id)
    form = SampleDeliveryForm(
        data=request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        product = form.cleaned_data['product']
        quantity = form.cleaned_data['quantity'] or 1
        try:
            give_sample_to_customer(customer, product, quantity, user=request.user)
            msg = _('Sample given: %(product)s x%(qty)s') % {'product': product.name, 'qty': quantity}
            messages.success(request, msg)
            return redirect('customers:customer_detail', pk=customer_id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('customers:customer_detail', pk=customer_id)
    return render(request, 'crm/sample_form_customer.html', {'customer': customer, 'form': form})


@login_required
@permission_required('crm.delete_lead', raise_exception=True)
def lead_delete(request, pk):
    """Soft delete lead - sets deleted_at."""
    lead = get_object_or_404(Lead.objects.filter(deleted_at__isnull=True), pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            lead.deleted_at = timezone.now()
            lead.save()
        messages.success(request, _('Lead deleted successfully.'))
        return redirect('crm:lead_list')

    context = {
        'title': _('Delete Lead'),
        'lead': lead,
    }
    return render(request, 'crm/lead_confirm_delete.html', context)


@login_required
@permission_required('crm.delete_sampledelivery', raise_exception=True)
def sample_delete(request, sample_id):
    """Soft delete sample delivery."""
    sample = get_object_or_404(
        SampleDelivery.objects.select_related('lead', 'customer', 'product'),
        pk=sample_id
    )
    if request.method == 'POST':
        with transaction.atomic():
            sample.soft_delete()
        messages.success(request, _('Sample delivery deleted successfully.'))
        return _sample_redirect(sample)

    context = {
        'title': _('Delete Sample Delivery'),
        'sample': sample,
    }
    return render(request, 'crm/sample_confirm_delete.html', context)


@login_required
@permission_required('crm.change_lead', raise_exception=True)
def lead_convert(request, pk):
    """Convert lead to customer using ModelForm."""
    lead = get_object_or_404(Lead.objects.filter(deleted_at__isnull=True), pk=pk)
    customer_types = CustomerType.objects.filter(is_active=True).order_by('sort_order', 'code')
    if not customer_types.exists():
        messages.error(
            request,
            _('No customer types found. Add in Admin → Master Data.')
        )
        return redirect('crm:lead_detail', pk=pk)

    form = LeadConvertForm(
        data=request.POST if request.method == 'POST' else None,
        initial={'customer_type': customer_types.first()} if customer_types.exists() else {},
    )
    if request.method == 'POST' and form.is_valid():
        customer = convert_lead_to_customer(
            lead, form.cleaned_data['customer_type'], user=request.user
        )
        messages.success(request, _('Lead converted to customer: %(name)s') % {'name': customer.name})
        return redirect('customers:customer_detail', pk=customer.pk)
    return render(request, 'crm/lead_convert.html', {
        'lead': lead,
        'form': form,
    })
