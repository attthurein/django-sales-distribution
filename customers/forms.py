"""
Customer forms.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Customer, CustomerPhoneNumber, Salesperson, SalespersonPhoneNumber
from master_data.models import CustomerType, Township
from common.utils import get_regions_with_townships


class CustomerForm(forms.ModelForm):
    township = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_township'}),
        label=_('Township'),
    )

    class Meta:
        model = Customer
        fields = [
            'name', 'shop_name', 'contact_person', 'phone', 'customer_type', 'township',
            'salesperson', 'street_address', 'credit_limit', 'payment_terms_days', 'is_active'
        ]
        widgets = {
            'street_address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        regions = get_regions_with_townships()
        township_choices = [('', _('Select township...'))]
        for region in regions:
            for t in region.townships.all():
                township_choices.append((str(t.id), t.name_en))
        self.fields['township'].choices = township_choices
        if self.instance and self.instance.pk and self.instance.township_id:
            self.fields['township'].initial = str(self.instance.township_id)

    def clean_township(self):
        val = self.cleaned_data.get('township')
        if not val:
            return None
        try:
            return Township.objects.get(pk=int(val))
        except (Township.DoesNotExist, ValueError):
            return None


class CustomerPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = CustomerPhoneNumber
        fields = ['phone', 'notes']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Notes')}),
        }


CustomerPhoneNumberFormSet = forms.inlineformset_factory(
    Customer, CustomerPhoneNumber,
    form=CustomerPhoneNumberForm,
    extra=0,
    can_delete=True
)


class SalespersonForm(forms.ModelForm):
    class Meta:
        model = Salesperson
        fields = ['name', 'phone', 'user', 'is_active']


class SalespersonPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = SalespersonPhoneNumber
        fields = ['phone', 'notes']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Notes')}),
        }


SalespersonPhoneNumberFormSet = forms.inlineformset_factory(
    Salesperson, SalespersonPhoneNumber,
    form=SalespersonPhoneNumberForm,
    extra=0,
    can_delete=True
)
