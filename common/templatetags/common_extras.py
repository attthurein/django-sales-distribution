"""
Common template tags and filters.
"""
from django import template
from django.utils.translation import get_language

register = template.Library()


@register.simple_tag
def currency_suffix():
    """
    Return the currency symbol/suffix from CompanySetting.base_currency.
    Affects whole system: invoices, reports, dashboard.
    Falls back to Ks/ကျပ် if no base_currency set.
    """
    from master_data.models import CompanySetting

    setting = CompanySetting.objects.select_related(
        'base_currency'
    ).first()
    if setting and setting.base_currency:
        curr = setting.base_currency
        lang = get_language()
        if lang == 'my' and curr.name_my:
            return curr.name_my
        if curr.symbol:
            return curr.symbol
        return curr.name_en
    return "ကျပ်" if get_language() == "my" else "Ks"


@register.filter
def master_name(obj):
    """
    Return the display name of a master data object (OrderStatus, CustomerType, etc.)
    based on the current language. Uses get_display_name(lang) if available,
    otherwise falls back to name_en.
    """
    if obj is None:
        return ''
    if hasattr(obj, 'get_display_name'):
        return obj.get_display_name(get_language())
    if hasattr(obj, 'name_my') and get_language() == 'my':
        return obj.name_my or obj.name_en
    if hasattr(obj, 'name_en'):
        return obj.name_en
    return str(obj)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified parameters added or changed.
    
    It also removes any empty parameters to keep the URL clean.
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    
    return query.urlencode()


@register.filter(name='abs')
def abs_filter(value):
    """Return the absolute value."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value
