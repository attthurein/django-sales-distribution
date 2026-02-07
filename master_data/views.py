"""
Master Data views.
"""
from django.contrib.auth.decorators import login_required, permission_required
from common.utils import get_regions_with_townships
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import CompanySetting
from .forms import CompanySettingForm
from .utils import has_transactional_data


@login_required
@permission_required('master_data.change_companysetting', raise_exception=True)
def company_setting(request):
    """View and edit company settings (singleton)."""
    instance = CompanySetting.objects.first()
    regions = get_regions_with_townships()

    if request.method == 'POST':
        form = CompanySettingForm(
            request.POST, request.FILES, instance=instance,
            base_currency_locked=has_transactional_data(),
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, _('Company settings saved successfully.')
            )
            return redirect('master_data:company_setting')
    else:
        form = CompanySettingForm(
            instance=instance,
            base_currency_locked=has_transactional_data(),
        )

    return render(request, 'master_data/company_setting_form.html', {
        'form': form,
        'setting': instance,
        'regions': regions,
        'base_currency_locked': has_transactional_data(),
    })
