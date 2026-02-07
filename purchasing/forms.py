"""
Purchasing forms - PurchaseOrder create, receive.
"""
from django import forms
from master_data.models import Supplier


class PurchaseOrderCreateForm(forms.Form):
    """Form for purchase order header - supplier, expected_date, notes."""

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True).order_by('name_en'),
        label='Supplier',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    expected_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )


class PurchaseReceiveItemForm(forms.Form):
    """Form for single receive item - item_id (hidden), received_quantity."""

    item_id = forms.IntegerField(widget=forms.HiddenInput())
    received_quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '0'}),
    )
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def clean_received_quantity(self):
        value = self.cleaned_data.get('received_quantity') or 0
        if value < 0:
            raise forms.ValidationError('Must be non-negative.')
        return value
