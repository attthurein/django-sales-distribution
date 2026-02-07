"""
Master Data context processors.
"""
from .models import CompanySetting


def company_setting(request):
    """
    Add company setting to template context for navbar, footer, etc.
    Returns dict with 'company_setting' key (CompanySetting instance or None).
    """
    setting = CompanySetting.objects.first()
    return {'company_setting': setting}
