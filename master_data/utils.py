"""
Master Data utilities.
"""
from django.apps import apps


def has_transactional_data():
    """
    Return True if system has any transactional data (excluding master data).
    When True, base currency cannot be changed.
    """
    models_to_check = [
        ('orders', 'SalesOrder'),
        ('orders', 'Payment'),
        ('returns', 'ReturnRequest'),
        ('purchasing', 'PurchaseOrder'),
        ('accounting', 'Expense'),
        ('core', 'Product'),
        ('customers', 'Customer'),
    ]
    for app_label, model_name in models_to_check:
        try:
            model = apps.get_model(app_label, model_name)
            if model.objects.exists():
                return True
        except LookupError:
            continue
    return False
