"""
Management command to find and clean duplicate customers.
Duplicates: same phone, or same name + phone.
Usage: python manage.py clean_duplicate_customers [--dry-run] [--yes]
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from customers.models import Customer


class Command(BaseCommand):
    help = 'Find and remove/merge duplicate customers (by phone or name+phone)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only report duplicates, do not delete',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_confirm = options['yes']

        # Find duplicates by phone
        phone_dupes = (
            Customer.objects.filter(deleted_at__isnull=True, is_active=True)
            .values('phone')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        to_merge = []
        for row in phone_dupes:
            customers = list(
                Customer.objects.filter(phone=row['phone'], deleted_at__isnull=True)
                .order_by('created_at')
            )
            if len(customers) > 1:
                # Keep oldest, mark others for merge/delete
                to_merge.append({
                    'keep': customers[0],
                    'duplicates': customers[1:],
                    'reason': f"Same phone: {row['phone']}",
                })

        if not to_merge:
            self.stdout.write(self.style.SUCCESS('No duplicate customers found.'))
            return

        self.stdout.write(f'\nFound {len(to_merge)} group(s) of duplicate customers:\n')
        for i, group in enumerate(to_merge, 1):
            self.stdout.write(f"  {i}. {group['reason']}")
            self.stdout.write(f"     Keep: {group['keep'].id} - {group['keep'].name} ({group['keep'].phone})")
            for d in group['duplicates']:
                self.stdout.write(f"     Remove: {d.id} - {d.name} ({d.phone})")
            self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run - no changes made.'))
            return

        if not skip_confirm:
            confirm = input('Proceed with soft-delete of duplicates? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Aborted.')
                return

        from django.utils import timezone
        deleted = 0
        for group in to_merge:
            for d in group['duplicates']:
                d.deleted_at = timezone.now()
                d.is_active = False
                d.save()
                deleted += 1
                self.stdout.write(f'  Soft-deleted customer {d.id}: {d.name}')

        self.stdout.write(self.style.SUCCESS(f'\nSoft-deleted {deleted} duplicate customer(s).'))
