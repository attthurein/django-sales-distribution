"""
Common utilities - Myanmar phone validation, formatting, shared querysets.
"""
import re
from decimal import Decimal

from django.db.models import Prefetch

from master_data.models import Region, Township, Country

# Myanmar numerals for display formatting
MYANMAR_DIGITS = '၀၁၂၃၄၅၆၇၈၉'


def validate_myanmar_phone(phone):
    """Validate Myanmar phone: 09xxxxxxxx, +959xxxxxxxx, 01xxxxxxxx."""
    if not phone:
        return False
    cleaned = re.sub(r'[\s\-]', '', str(phone))
    patterns = [
        r'^09\d{7,9}$',
        r'^\+959\d{7,9}$',
        r'^01\d{6,8}$',
    ]
    return any(re.match(p, cleaned) for p in patterns)


def format_myanmar_phone(phone):
    """Display formatting for Myanmar phone."""
    if not phone:
        return ''
    cleaned = re.sub(r'[\s\-]', '', str(phone))
    if cleaned.startswith('+959'):
        return f"+959 {cleaned[4:7]} {cleaned[7:]}"
    if cleaned.startswith('09'):
        return f"09 {cleaned[2:5]} {cleaned[5:]}"
    return phone


def format_amount_mmk(amount, use_myanmar_numerals=False):
    """Format amount as MMK with thousand separators."""
    if amount is None:
        return ''
    try:
        val = Decimal(str(amount))
        formatted = f"{val:,.0f}"
        if use_myanmar_numerals:
            formatted = ''.join(
                MYANMAR_DIGITS[int(c)] if c.isdigit() else c
                for c in formatted
            )
        return f"{formatted} ကျပ်"
    except (ValueError, TypeError):
        return str(amount)


def get_master_display_name(obj, lang='en'):
    """Return name_en or name_my based on language for master models."""
    if obj is None:
        return ''
    if hasattr(obj, 'get_display_name'):
        return obj.get_display_name(lang)
    if hasattr(obj, 'name_my') and lang == 'my' and obj.name_my:
        return obj.name_my
    if hasattr(obj, 'name_en'):
        return obj.name_en
    return str(obj)


def get_regions_with_townships():
    """
    Return Region queryset with active townships prefetched.
    Use for forms/views that need region-township dropdowns (DRY).
    """
    return Region.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'townships',
            queryset=Township.objects.filter(is_active=True).order_by('name_en')
        )
    ).order_by('country__sort_order', 'country__name_en', 'name_en')


def get_countries_with_regions():
    """
    Return Country queryset with active regions and townships prefetched.
    """
    return Country.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'regions',
            queryset=Region.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'townships',
                    queryset=Township.objects.filter(is_active=True).order_by('name_en')
                )
            ).order_by('name_en')
        )
    ).order_by('name_en')


def reset_model_sequences(models_list):
    """
    Reset database auto-increment counters for the given models.
    Supports SQLite and PostgreSQL.
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            # SQLite: Delete from sqlite_sequence
            table_names = [model._meta.db_table for model in models_list]
            if table_names:
                placeholders = ', '.join(['%s'] * len(table_names))
                cursor.execute(
                    f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})",
                    table_names
                )
        elif connection.vendor == 'postgresql':
            # PostgreSQL: ALTER SEQUENCE RESTART WITH 1
            for model in models_list:
                db_table = model._meta.db_table
                seq_name = f"{db_table}_id_seq"
                try:
                    cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1;")
                except Exception:
                    # Sequence might be named differently or not exist
                    pass
