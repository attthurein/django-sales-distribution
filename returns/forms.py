"""
Return forms - ModelForm for return creation.
"""
from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from master_data.models import ReturnType, ReturnReason


class ReturnItemForm(forms.Form):
    """Form for single return item - order_item_id (hidden), quantity, reason, condition_notes."""

    order_item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0, 'placeholder': '0'}),
    )
    reason = forms.ModelChoiceField(
        queryset=ReturnReason.objects.all().order_by('name_en'),
        required=False,
        empty_label='--',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    return_to_stock = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'title': 'Return to sellable stock'}),
        label='Restock'
    )
    condition_notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': ''}),
    )

    def clean_quantity(self):
        value = self.cleaned_data.get('quantity') or 0
        if value < 0:
            raise forms.ValidationError('Must be non-negative.')
        return value


ReturnItemFormSet = formset_factory(
    ReturnItemForm,
    extra=0,
    min_num=0,
)


class ReturnOrderSelectForm(forms.Form):
    """Form for step 1: select order for return."""

    order_id = forms.ModelChoiceField(
        queryset=None,
        empty_label=_('-- Select Order --'),
        label=_('Order'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        orders_qs = kwargs.pop('orders_queryset', None)
        super().__init__(*args, **kwargs)
        if orders_qs is not None:
            self.fields['order_id'].queryset = orders_qs


class ReturnCreateForm(forms.Form):
    """Form for step 2: return type and notes."""

    return_type = forms.ModelChoiceField(
        queryset=ReturnType.objects.all().order_by('name_en'),
        label='Return Type',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )
