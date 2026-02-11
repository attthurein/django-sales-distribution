"""
Master Data forms.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CompanySetting, Township, Currency, Region, Country, Supplier, SupplierPhoneNumber
from .utils import has_transactional_data
from common.utils import get_regions_with_townships, get_countries_with_regions


class CompanySettingForm(forms.ModelForm):
    """Form for company settings (singleton)."""
    country_id = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_country'}),
        label=_('Country'),
    )
    region_id = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_region'}),
        label=_('Region'),
    )
    township = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_township'}),
        label=_('Township'),
    )

    class Meta:
        model = CompanySetting
        fields = [
            'name', 'shop_name', 'logo', 'address', 'phone', 'email', 'tax_id',
            'footer_text', 'region', 'township', 'base_currency', 'default_country',
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Company name'}
            ),
            'shop_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Shop name'}
            ),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2}
            ),
            'base_currency': forms.Select(attrs={'class': 'form-select'}),
            'default_country': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.base_currency_locked = kwargs.pop('base_currency_locked', None)
        if self.base_currency_locked is None:
            self.base_currency_locked = has_transactional_data()
        super().__init__(*args, **kwargs)
        self.fields.pop('region', None)
        self.fields.pop('township', None)
        countries = get_countries_with_regions()

        country_choices = [('', '---')] + [
            (str(c.id), c.name) for c in countries
        ]
        
        region_choices = [('', '---')]
        township_choices = [('', '---')]
        
        for country in countries:
            for region in country.regions.all():
                region_choices.append((str(region.id), region.name))
                for t in region.townships.all():
                    township_choices.append((str(t.id), t.name))

        self.fields['country_id'] = forms.ChoiceField(
            required=False,
            choices=country_choices,
            widget=forms.Select(
                attrs={'class': 'form-select', 'id': 'id_country'}
            ),
            label=_('Country'),
        )
        self.fields['region_id'] = forms.ChoiceField(
            required=False,
            choices=region_choices,
            widget=forms.Select(
                attrs={'class': 'form-select', 'id': 'id_region'}
            ),
            label=_('Region'),
        )
        self.fields['township'] = forms.ChoiceField(
            required=False,
            choices=township_choices,
            widget=forms.Select(
                attrs={'class': 'form-select', 'id': 'id_township'}
            ),
            label=_('Township'),
        )

        if self.instance and self.instance.pk:
            if self.instance.township:
                self.fields['township'].initial = str(self.instance.township.id)
                if self.instance.township.region:
                    self.fields['region_id'].initial = str(self.instance.township.region.id)
                    if self.instance.township.region.country:
                        self.fields['country_id'].initial = str(self.instance.township.region.country.id)
            elif self.instance.region:
                self.fields['region_id'].initial = str(self.instance.region.id)
                if self.instance.region.country:
                    self.fields['country_id'].initial = str(self.instance.region.country.id)

        if self.base_currency_locked:
            self.fields['base_currency'].disabled = True
            self.fields['base_currency'].help_text = _(
                "Currency cannot be changed because there are existing transactions."
            )

    def clean_township(self):
        val = self.cleaned_data.get('township')
        if not val:
            return None
        try:
            return Township.objects.get(pk=int(val))
        except (Township.DoesNotExist, ValueError):
            return None


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['code', 'name_en', 'name_my', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'name_my': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = SupplierPhoneNumber
        fields = ['phone', 'notes']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Notes')}),
        }


SupplierPhoneNumberFormSet = forms.inlineformset_factory(
    Supplier, SupplierPhoneNumber,
    form=SupplierPhoneNumberForm,
    extra=0,
    can_delete=True
)
