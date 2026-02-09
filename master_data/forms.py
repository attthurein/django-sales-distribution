"""
Master Data forms.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CompanySetting, Township, Currency, Region, Country
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
            'name', 'logo', 'address', 'phone', 'email', 'tax_id',
            'footer_text', 'region', 'township', 'base_currency',
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Company name'}
            ),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2}
            ),
            'base_currency': forms.Select(attrs={'class': 'form-select'}),
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
            if self.instance.region_id:
                self.fields['region_id'].initial = str(
                    self.instance.region_id
                )
                if self.instance.region.country_id:
                     self.fields['country_id'].initial = str(self.instance.region.country_id)
            if self.instance.township_id:
                self.fields['township'].initial = str(
                    self.instance.township_id
                )

        self.fields['base_currency'].queryset = Currency.objects.filter(
            is_active=True
        ).order_by('sort_order', 'code')
        self.fields['base_currency'].empty_label = '---'
        self.fields['base_currency'].required = False

    def clean_base_currency(self):
        """Reject base_currency change when transactional data exists."""
        if self.base_currency_locked:
            if self.instance and self.instance.pk:
                return self.instance.base_currency
            return None
        return self.cleaned_data.get('base_currency')

    def clean_township(self):
        val = self.cleaned_data.get('township')
        if not val:
            return None
        try:
            return Township.objects.get(pk=int(val))
        except (Township.DoesNotExist, ValueError):
            return None

    def clean_region_id(self):
        val = self.cleaned_data.get('region_id')
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            return None

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.region_id = self.cleaned_data.get('region_id')
        obj.township = self.cleaned_data.get('township')
        if commit:
            obj.save()
        return obj
