from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from common.models import AuditLog, AuditLogArchive

class Command(BaseCommand):
    help = 'Archive audit logs older than 6 months to AuditLogArchive table.'

    def handle(self, *args, **options):
        self.stdout.write("Starting audit log archiving...")
        
        # Calculate cutoff date (6 months ago)
        cutoff_date = timezone.now() - timedelta(days=6*30)
        self.stdout.write(f"Archiving logs created before: {cutoff_date}")
        
        # Get logs to archive
        logs_to_archive = AuditLog.objects.filter(created_at__lt=cutoff_date)
        count = logs_to_archive.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No logs to archive."))
            return

        self.stdout.write(f"Found {count} logs to archive. Processing...")
        
        # Process in chunks to avoid memory issues
        chunk_size = 1000
        processed_count = 0
        
        while processed_count < count:
            # Get current chunk IDs
            # We slice the queryset. Note: We cannot use iterator() easily with delete 
            # inside the loop if we modify the table, but here we are moving data.
            # Safe way: fetch IDs of first N records
            chunk_qs = logs_to_archive[:chunk_size]
            chunk_logs = list(chunk_qs)
            
            if not chunk_logs:
                break
                
            archive_entries = []
            log_ids = []
            
            for log in chunk_logs:
                archive_entries.append(AuditLogArchive(
                    user_id=log.user_id,
                    action=log.action,
                    model_name=log.model_name,
                    object_id=log.object_id,
                    changes=log.changes,
                    ip_address=log.ip_address,
                    created_at=log.created_at
                ))
                log_ids.append(log.id)
            
            with transaction.atomic():
                # Bulk create archives
                AuditLogArchive.objects.bulk_create(archive_entries)
                # Delete originals
                AuditLog.objects.filter(id__in=log_ids).delete()
                
            processed_count += len(chunk_logs)
            self.stdout.write(f"Archived {processed_count}/{count} logs...")
            
        self.stdout.write(self.style.SUCCESS(f"Successfully archived {processed_count} logs."))
