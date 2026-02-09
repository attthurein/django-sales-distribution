"""
Backup database using Django dumpdata.
Saves to backups/ directory with timestamp.
Deletes backups older than --keep-days (default: 30).
Usage: python manage.py backup_db
"""
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Backup database to JSON file (uses dumpdata). Removes old backups.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to save backup files (default: backups/)',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Delete backups older than this many days (default: 30, 0=keep all)',
        )
        parser.add_argument(
            '--exclude',
            nargs='*',
            default=['contenttypes', 'sessions', 'admin.logentry'],
            help='Apps to exclude from backup',
        )

    def _cleanup_old_backups(self, output_dir, keep_days):
        """Remove backup files older than keep_days."""
        if keep_days <= 0:
            return 0
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        for f in output_dir.glob('backup_*.json'):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    removed += 1
                    self.stdout.write(f'  Removed old backup: {f.name}')
            except OSError as e:
                self.stdout.write(self.style.WARNING(f'  Could not remove {f}: {e}'))
        return removed

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        exclude = options['exclude']
        keep_days = options['keep_days']

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f'backup_{timestamp}.json'

        self.stdout.write(f'Creating backup: {filename}')

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent', '2',
                    exclude=exclude,
                    stdout=f,
                )
            self.stdout.write(self.style.SUCCESS(f'Backup saved: {filename}'))

            if keep_days > 0:
                removed = self._cleanup_old_backups(output_dir, keep_days)
                if removed:
                    self.stdout.write(self.style.SUCCESS(f'Removed {removed} old backup(s)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Backup failed: {e}'))
            raise
