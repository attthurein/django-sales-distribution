"""
Customer forms.
"""
from django import forms
from .models import Customer, Salesperson
from master_data.models import CustomerType, Township
from common.utils import get_regions_with_townships


class CustomerForm(forms.ModelForm):
    township = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_township'}),
        label='Township',
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
        township_choices = [('', 'Select township...')]
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


class SalespersonForm(forms.ModelForm):
    class Meta:
        model = Salesperson
        fields = ['name', 'phone', 'user', 'is_active']
