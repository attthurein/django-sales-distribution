"""
Reset all data EXCEPT Master Data.
Keeps: master_data models, auth.User, sessions, admin.LogEntry (for admin).
Deletes: Customers, Orders, Leads, Products, Returns, Purchasing, Stock, etc.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from returns.models import ReturnProcessing, ReturnItem, ReturnRequest
from orders.models import Payment, OrderItem, SalesOrder
from crm.models import SampleDelivery, ContactLog, Lead
from purchasing.models import PurchaseItem, PurchaseOrder
from core.models import StockMovement, Batch, ProductPriceTier, ProductVariant, Product
from accounting.models import Expense, ExpenseCategory
from customers.models import Customer, Salesperson
from common.models import AuditLog


class Command(BaseCommand):
    help = 'Reset all data except Master Data (CustomerType, Region, Township, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt (use with caution!)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        models_to_reset = [
            (ReturnProcessing, 'ReturnProcessing'),
            (ReturnItem, 'ReturnItem'),
            (ReturnRequest, 'ReturnRequest'),
            (Payment, 'Payment'),
            (OrderItem, 'OrderItem'),
            (SalesOrder, 'SalesOrder'),
            (SampleDelivery, 'SampleDelivery'),
            (ContactLog, 'ContactLog'),
            (Lead, 'Lead'),
            (PurchaseItem, 'PurchaseItem'),
            (PurchaseOrder, 'PurchaseOrder'),
            (StockMovement, 'StockMovement'),
            (Batch, 'Batch'),
            (ProductPriceTier, 'ProductPriceTier'),
            (ProductVariant, 'ProductVariant'),
            (Product, 'Product'),
            (Expense, 'Expense'),
            (ExpenseCategory, 'ExpenseCategory'),
            (Customer, 'Customer'),
            (Salesperson, 'Salesperson'),
            (AuditLog, 'AuditLog'),
        ]

        if options['dry_run']:
            self.stdout.write('Dry run - counts only (no deletion):')
            total = 0
            for model, name in models_to_reset:
                count = model.objects.count()
                total += count
                self.stdout.write(f'  - {name}: {count}')
            self.stdout.write(self.style.WARNING(f'Total: {total} records would be deleted.'))
            self.stdout.write('Master Data (CustomerType, Region, Township, etc.) would be KEPT.')
            return

        if not options['no_input']:
            confirm = input(
                'This will DELETE all Customers, Orders, Leads, Products, Returns, '
                'Purchasing, Stock, etc. Master Data will be KEPT. Continue? [y/N]: '
            )
            if confirm.lower() != 'y':
                self.stdout.write('Aborted.')
                return

        with transaction.atomic():
            deleted = {}
            for model, name in models_to_reset:
                if hasattr(model, 'all_objects'):
                    # Use all_objects to ensure hard delete for SoftDeleteMixin models
                    deleted[name] = model.all_objects.all().delete()[0]
                else:
                    deleted[name] = model.objects.all().delete()[0]

        total = sum(deleted.values())
        self.stdout.write(self.style.SUCCESS(
            f'Data reset complete. Deleted {total} records across {len(deleted)} models.'
        ))
        for model, count in deleted.items():
            if count:
                self.stdout.write(f'  - {model}: {count}')
