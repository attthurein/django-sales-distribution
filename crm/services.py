"""
CRM services - sample give, lead convert.
Business logic lives here; views stay thin.
"""
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import SampleDelivery
from customers.models import Customer
from core.services import deduct_stock
from master_data.constants import SAMPLE_STATUS_GIVEN, LEAD_STATUS_CONTACTED, LEAD_STATUS_SAMPLE_GIVEN, LEAD_STATUS_CONVERTED


from customers.models import Customer, CustomerPhoneNumber


def convert_lead_to_customer(lead, customer_type, user=None):
    """
    Convert lead to customer. Creates or updates customer, links lead.
    Excludes soft-deleted customers; restores if same phone was previously deleted.
    Returns Customer.
    """
    with transaction.atomic():
        customer = Customer.objects.filter(
            phone=lead.phone, deleted_at__isnull=True
        ).first()
        if customer:
            customer.name = lead.name
            customer.shop_name = lead.shop_name or ''
            customer.contact_person = lead.contact_person or ''
            customer.street_address = lead.address or ''
            customer.township_id = lead.township_id
            customer.save()
        else:
            deleted = Customer.objects.filter(phone=lead.phone).exclude(
                deleted_at__isnull=True
            ).first()
            if deleted:
                deleted.deleted_at = None
                deleted.is_active = True
                deleted.name = lead.name
                deleted.shop_name = lead.shop_name or ''
                deleted.contact_person = lead.contact_person or ''
                deleted.street_address = lead.address or ''
                deleted.township_id = lead.township_id
                deleted.customer_type = customer_type
                deleted.save()
                customer = deleted
            else:
                customer = Customer.objects.create(
                    phone=lead.phone,
                    name=lead.name,
                    shop_name=lead.shop_name or '',
                    contact_person=lead.contact_person or '',
                    street_address=lead.address or '',
                    customer_type=customer_type,
                    township_id=lead.township_id,
                )
        
        # Copy additional phones
        for lead_phone in lead.additional_phones.all():
            CustomerPhoneNumber.objects.get_or_create(
                customer=customer,
                phone=lead_phone.phone,
                defaults={'notes': lead_phone.notes}
            )

        lead.customer = customer
        lead.status = LEAD_STATUS_CONVERTED
        lead.save()
    return customer


def give_sample_to_lead(lead, product, quantity, user=None):
    """
    Give sample to lead. Deducts stock, creates SampleDelivery.
    Returns SampleDelivery. Raises ValueError on failure.
    """
    if quantity <= 0:
        quantity = 1
    if quantity > product.stock_quantity:
        raise ValueError(
            _('Insufficient stock. Available: %(qty)s') % {'qty': product.stock_quantity}
        )

    with transaction.atomic():
        sample = SampleDelivery.objects.create(
            lead=lead,
            product=product,
            quantity=quantity,
            status=SAMPLE_STATUS_GIVEN,
            created_by=user,
        )
        deduct_stock(
            product_id=product.id,
            quantity=quantity,
            reference_type='SampleDelivery',
            reference_id=sample.id,
            user=user,
        )
        if lead.status == LEAD_STATUS_CONTACTED:
            lead.status = LEAD_STATUS_SAMPLE_GIVEN
            lead.save(update_fields=['status'])
    return sample


def give_sample_to_customer(customer, product, quantity, user=None):
    """
    Give sample to customer. Deducts stock, creates SampleDelivery.
    Returns SampleDelivery. Raises ValueError on failure.
    """
    if quantity <= 0:
        quantity = 1
    if quantity > product.stock_quantity:
        raise ValueError(
            _('Insufficient stock. Available: %(qty)s') % {'qty': product.stock_quantity}
        )

    with transaction.atomic():
        sample = SampleDelivery.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            status=SAMPLE_STATUS_GIVEN,
            created_by=user,
        )
        deduct_stock(
            product_id=product.id,
            quantity=quantity,
            reference_type='SampleDelivery',
            reference_id=sample.id,
            user=user,
        )
    return sample
