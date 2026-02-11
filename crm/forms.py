"""
CRM forms - ModelForm for Lead, ContactLog, SampleDelivery.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Lead, LeadPhoneNumber, ContactLog, SampleDelivery
from master_data.constants import LEAD_STATUS_NEW
from common.utils import get_countries_with_regions


class TownshipSelectWithRegion(forms.Select):
    """Select widget that adds data-region-id to options for JS filtering."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value and hasattr(self, 'region_map'):
            # Convert value to string because region_map keys are strings
            val_str = str(value)
            if val_str in self.region_map:
                option['attrs']['data-region-id'] = str(self.region_map[val_str])
        return option


class LeadForm(forms.ModelForm):
    """ModelForm for Lead create/edit."""

    class Meta:
        model = Lead
        fields = [
            'name',
            'shop_name',
            'contact_person',
            'phone',
            'address',
            'township',
            'source',
            'status',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'township': TownshipSelectWithRegion(attrs={'class': 'form-select'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['township'].required = False
        qs = self.fields['township'].queryset.filter(
            is_active=True
        ).select_related('region').order_by('region__name_en', 'name_en')
        self.fields['township'].queryset = qs
        # Add region_id map for widget to render data-region-id on options
        self.fields['township'].widget.region_map = {
            str(t.id): t.region_id for t in qs
        }
        if not self.instance.pk:
            self.fields['status'].widget = forms.HiddenInput()
            self.initial['status'] = LEAD_STATUS_NEW


class LeadPhoneNumberForm(forms.ModelForm):
    """Form for additional phone numbers."""
    class Meta:
        model = LeadPhoneNumber
        fields = ['phone', 'notes']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Notes (e.g. Office)')}),
        }


LeadPhoneNumberFormSet = forms.inlineformset_factory(
    Lead, LeadPhoneNumber,
    form=LeadPhoneNumberForm,
    extra=0,
    can_delete=True
)


class ContactLogForm(forms.ModelForm):
    """ModelForm for adding contact log to lead."""

    class Meta:
        model = ContactLog
        fields = ['contact_type', 'notes', 'next_follow_up']
        widgets = {
            'contact_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'next_follow_up': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from master_data.models import ContactType
        self.fields['contact_type'].queryset = ContactType.objects.filter(
            is_active=True
        ).order_by('sort_order', 'code')
        self.fields['notes'].required = True


class SampleDeliveryForm(forms.ModelForm):
    """ModelForm for giving sample to lead/customer."""

    class Meta:
        model = SampleDelivery
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = self.fields['product'].queryset.filter(
            is_active=True
        ).select_related('unit').order_by('name')

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity or 1

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity') or 1
        if product and quantity and quantity > product.stock_quantity:
            raise forms.ValidationError(
                'Insufficient stock. Available: %(qty)s' % {'qty': product.stock_quantity}
            )
        return cleaned


class LeadConvertForm(forms.Form):
    """Form for converting lead to customer - customer type selection."""

    customer_type = forms.ModelChoiceField(
        queryset=None,
        label='Customer Type',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from master_data.models import CustomerType
        self.fields['customer_type'].queryset = CustomerType.objects.filter(
            is_active=True
        ).order_by('sort_order', 'code')
