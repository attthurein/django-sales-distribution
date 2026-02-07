"""
Order forms.
"""
from decimal import Decimal
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import SalesOrder, Payment
from customers.models import Customer


class OrderCreateForm(forms.Form):
    """Form for order create - customer, is_pre_order, discount_amount, notes."""

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).select_related('customer_type').order_by('name'),
        label='Customer',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'customer_id'}),
    )
    is_pre_order = forms.BooleanField(
        required=False,
        initial=False,
        label='Pre-order',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is_pre_order'}),
    )
    discount_amount = forms.DecimalField(
        required=False,
        initial=Decimal('0'),
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'min': 0, 'step': '0.01', 'id': 'discount_amount',
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2, 'id': 'notes',
            'placeholder': _('Optional notes'),
        }),
    )


class OrderForm(forms.ModelForm):
    """Order form for editing (customer, notes). Salesperson was removed."""

    class Meta:
        model = SalesOrder
        fields = ['customer', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).select_related('customer_type').order_by('name')


class OrderUpdateForm(forms.ModelForm):
    """Form for updating order status, delivery_date, notes."""

    class Meta:
        model = SalesOrder
        fields = ['status', 'delivery_date', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from master_data.models import OrderStatus
        self.fields['status'].queryset = OrderStatus.objects.filter(
            is_active=True
        ).order_by('sort_order', 'code')


class PaymentForm(forms.ModelForm):
    """ModelForm for adding payment to order."""

    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'class': 'form-control'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from master_data.models import PaymentMethod
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
            is_active=True
        ).order_by('name_en')
        self.fields['payment_method'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount
