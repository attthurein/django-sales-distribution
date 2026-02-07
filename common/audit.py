"""
Audit logging - track who changed what and when.
Uses thread-local to get current user from request (set by middleware).
"""
import logging
import threading

from django.db.models.signals import pre_save, post_save, post_delete
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def get_current_user():
    """Get the current user from thread-local (set by middleware)."""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """Set the current user in thread-local."""
    _thread_locals.user = user


# Models to audit (Django model_name is lowercase: app_label.model_name)
AUDITED_MODELS = [
    'customers.customer',
    'customers.salesperson',
    'core.product',
    'core.productvariant',
    'core.batch',
    'orders.salesorder',
    'orders.orderitem',
    'orders.payment',
    'returns.returnrequest',
    'returns.returnitem',
    'crm.lead',
    'crm.contactlog',
    'crm.sampledelivery',
    'purchasing.purchaseorder',
    'purchasing.purchaseitem',
    'accounting.expense',
    'accounting.expensecategory',
    'master_data.township',
    'master_data.taxrate',
    'master_data.promotion',
    'master_data.customertype',
    'master_data.returnreason',
    'master_data.returntype',
    'master_data.paymentmethod',
    'master_data.orderstatus',
    'master_data.returnrequeststatus',
    'master_data.productcategory',
    'master_data.unitofmeasure',
    'master_data.contacttype',
    'master_data.region',
    'master_data.deliveryroute',
    'master_data.supplier',
    'master_data.currency',
    'master_data.companysetting',
]

# Fields to skip when capturing changes (auto, internal)
SKIP_FIELDS = {'id', 'pk', 'created_at', 'updated_at'}


def _get_model_label(instance):
    """Return app_label.model_name (model_name is lowercase in Django)."""
    return f'{instance._meta.app_label}.{instance._meta.model_name}'


def _should_audit(instance):
    """Return True if instance's model is in AUDITED_MODELS."""
    label = _get_model_label(instance)
    return label in AUDITED_MODELS


def _to_json_safe(val, max_len=200):
    """Convert value to JSON-serializable form (datetime, date -> string)."""
    if val is None:
        return None
    if hasattr(val, 'pk'):  # Model instance (FK)
        return str(val)[:max_len]
    # datetime, date, Decimal, UUID, etc. -> string for JSON
    s = str(val)
    return s[:max_len] if len(s) > max_len else s


def _get_instance_values(instance, max_len=200):
    """Get dict of field values for audit (skip auto fields, limit length)."""
    values = {}
    for f in instance._meta.fields:
        if f.name in SKIP_FIELDS or getattr(f, 'auto_created', False):
            continue
        try:
            val = getattr(instance, f.name, None)
            values[f.name] = _to_json_safe(val, max_len)
        except (AttributeError, TypeError, KeyError) as e:
            logger.warning(
                'Audit: failed to get field %s.%s: %s',
                instance._meta.model_name, f.name, e,
                exc_info=True
            )
    return values


def _build_audit_changes(instance, created, new_values):
    """Build changes dict for create or update audit log."""
    if created:
        summary = _build_create_summary(instance, new_values)
        return {'new': new_values, 'summary': summary}
    key = (_get_model_label(instance), instance.pk)
    old_values = getattr(_thread_locals, 'audit_old', {}).get(key, {})
    diff = {
        k: {'old': old_values.get(k), 'new': new_val}
        for k, new_val in new_values.items()
        if old_values.get(k) != new_val
    }
    summary = (
        _build_update_summary(instance, diff) if diff else 'No field changes'
    )
    audit_old = getattr(_thread_locals, 'audit_old', None)
    if audit_old is not None and key in audit_old:
        del audit_old[key]
    return {'diff': diff, 'summary': summary}


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Store old values before update for comparison."""
    if sender.__name__ == 'AuditLog' or not _should_audit(instance):
        return
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            key = (_get_model_label(instance), instance.pk)
            if not hasattr(_thread_locals, 'audit_old'):
                _thread_locals.audit_old = {}
            _thread_locals.audit_old[key] = _get_instance_values(old)
        except sender.DoesNotExist:
            # Expected for new instances (create flow)
            pass


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Log create and update actions with before/after values."""
    if sender.__name__ == 'AuditLog':
        return
    if not _should_audit(instance):
        return
    from .models import AuditLog
    user = get_current_user()
    new_values = _get_instance_values(instance)
    changes = _build_audit_changes(instance, created, new_values)

    AuditLog.objects.create(
        user=user,
        action='create' if created else 'update',
        model_name=_get_model_label(instance),
        object_id=instance.pk,
        changes=changes,
    )


def _get_object_label(instance, max_len=80):
    """Get short label for the record (whose record)."""
    try:
        return str(instance)[:max_len] if instance else ''
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(
            'Audit: failed to get object label for %s pk=%s: %s',
            instance._meta.model_name if instance else '?',
            getattr(instance, 'pk', None),
            e,
        )
        return ''


def _build_create_summary(instance, new_values):
    """Build human-readable summary for create (whose + what)."""
    obj_label = _get_object_label(instance)
    parts = [str(v) for k, v in list(new_values.items())[:3] if v]
    detail = ', '.join(parts[:3]) if parts else ''
    if obj_label:
        return f'Created: {obj_label}' + (f' ({detail})' if detail else '')
    return 'Created: ' + detail if detail else 'Created'


def _build_update_summary(instance, diff):
    """Build human-readable summary for update (whose + what changed)."""
    obj_label = _get_object_label(instance)
    parts = []
    for field, vals in list(diff.items())[:5]:
        old_v = vals.get('old', '')
        new_v = vals.get('new', '')
        parts.append(f"{field}: {old_v} → {new_v}")
    changes = ' | '.join(parts) if parts else 'Updated'
    if obj_label:
        return f'{obj_label}: {changes}'
    return changes


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Log delete actions with deleted values."""
    if sender.__name__ == 'AuditLog':
        return
    if not _should_audit(instance):
        return
    from .models import AuditLog
    user = get_current_user()
    old_values = _get_instance_values(instance)
    summary = 'Deleted: ' + str(instance)[:100]
    AuditLog.objects.create(
        user=user,
        action='delete',
        model_name=_get_model_label(instance),
        object_id=instance.pk,
        changes={'old': old_values, 'summary': summary},
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    from .models import AuditLog

    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    username = credentials.get('username', 'unknown')

    AuditLog.objects.create(
        user=None,
        action='login_failed',
        model_name='auth.user',
        object_id=None,
        changes={'username': username, 'ip': ip, 'user_agent': request.META.get('HTTP_USER_AGENT', '')},
        ip_address=ip
    )
