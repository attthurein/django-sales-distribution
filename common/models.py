"""
Common models - Audit logging, Soft Delete functionality.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet for soft delete functionality."""
    
    def active(self):
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Return only deleted records."""
        return self.filter(deleted_at__isnull=False)
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of actual delete."""
        return self.soft_delete()

    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the record."""
        return super().delete(using=using, keep_parents=keep_parents)

    def soft_delete(self):
        """Soft delete all records in queryset."""
        count = self.update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}
    
    def restore(self):
        """Restore all soft deleted records in queryset."""
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    """Manager for soft delete functionality."""
    
    def get_queryset(self):
        """Return only active (non-deleted) records by default."""
        return SoftDeleteQuerySet(self.model, using=self._db).active()
    
    def all_with_deleted(self):
        """Return all records including deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """Return only deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()


class SoftDeleteMixin(models.Model):
    """Mixin to add soft delete functionality to models."""
    
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Deleted at"))
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access to all records including deleted
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['deleted_at']),
        ]
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of actual delete."""
        return self.soft_delete()

    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the record."""
        return super().delete(using=using, keep_parents=keep_parents)

    def soft_delete(self):
        """Soft delete this record."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return 1, {self._meta.label: 1}
    
    def restore(self):
        """Restore this soft deleted record."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    @property
    def is_deleted(self):
        """Check if record is soft deleted."""
        return self.deleted_at is not None


class AuditLog(models.Model):
    """Who changed what and when."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Audit log")
        verbose_name_plural = _("Audit logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name} #{self.object_id}"


class AuditLogArchive(models.Model):
    """Archived audit logs older than 6 months."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='audit_log_archives'
    )
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField()  # Not auto_now_add because we copy the original timestamp
    archived_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Audit log archive")
        verbose_name_plural = _("Audit log archives")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        return f"ARCHIVED: {self.action} - {self.model_name} #{self.object_id}"
