"""
Core forms - Product with price tiers.
"""
from django import forms
from django.utils.translation import gettext_lazy as _, get_language
from .models import Product, ProductPriceTier
from master_data.models import CustomerType


class ProductForm(forms.ModelForm):
    """Product form with optional price tier fields per customer type."""

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'category', 'unit',
            'base_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'expiry_date',
            'expiry_alert_days', 'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'sku': forms.TextInput(attrs={'placeholder': _('Optional')}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = _('-- Select Category --')
        self.fields['unit'].empty_label = _('-- Select Unit --')
        # Add price tier fields for each customer type
        lang = get_language()
        for ct in CustomerType.objects.filter(
                is_active=True
        ).order_by('sort_order'):
            field_name = f'price_{ct.code}'
            initial = None
            if self.instance and self.instance.pk:
                tier = ProductPriceTier.objects.filter(
                    product=self.instance, customer_type=ct
                ).first()
                if tier:
                    initial = tier.price
            
            ct_name = ct.get_display_name(lang)
            self.fields[field_name] = forms.DecimalField(
                max_digits=12, decimal_places=2,
                required=False,
                initial=initial,
                label=f'{_("Price")} ({ct_name})',
                widget=forms.NumberInput(
                    attrs={'step': '0.01', 'placeholder': _('Uses base if empty')}
                )
            )

    def save(self, commit=True):
        product = super().save(commit=commit)
        if commit:
            for ct in CustomerType.objects.filter(is_active=True):
                field_name = f'price_{ct.code}'
                value = self.cleaned_data.get(field_name)
                if value is not None:
                    ProductPriceTier.objects.update_or_create(
                        product=product, customer_type=ct,
                        defaults={'price': value}
                    )
                else:
                    ProductPriceTier.objects.filter(
                        product=product, customer_type=ct
                    ).delete()
        return product


class StockAdjustmentForm(forms.Form):
    """Form for manual stock adjustment. Uses core.services.adjust_stock."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        label='Product',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_adjust_product'}),
    )
    quantity = forms.IntegerField(
        label='Adjustment (+ to add, - to subtract)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 10 or -5',
            'step': 1,
        }),
        help_text='Positive to add stock, negative to subtract.',
    )
    expiry_date = forms.DateField(
        required=False,
        label='Expiry Date (for Batch)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Specify if adjusting a specific batch (required for adding new batch).',
    )
    reason = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for adjustment',
        }),
        help_text='Required for audit trail.',
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        if product:
            self.fields['product'].initial = product
            self.fields['product'].widget = forms.HiddenInput()

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity == 0:
            raise forms.ValidationError('Quantity must not be zero.')
        return quantity

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        if product and quantity and quantity < 0:
            if product.stock_quantity + quantity < 0:
                raise forms.ValidationError(
                    'Cannot reduce stock below zero. Current: %(stock)s, adjustment: %(adj)s'
                    % {'stock': product.stock_quantity, 'adj': quantity}
                )
        return cleaned
