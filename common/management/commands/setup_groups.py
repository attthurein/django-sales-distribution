"""
Create default groups with permissions for Django Golden Rules.
Run: python manage.py setup_groups
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Create default groups (Salesperson, Manager, Accountant) with permissions'

    def handle(self, *args, **options):
        # Salesperson: orders, returns, crm, customers, core (view)
        salesperson, _ = Group.objects.get_or_create(name='Salesperson')
        perms = Permission.objects.filter(
            codename__in=[
                'add_salesorder', 'change_salesorder', 'view_salesorder',
                'add_payment', 'view_payment',
                'add_returnrequest', 'view_returnrequest',
                'add_lead', 'change_lead', 'view_lead',
                'add_contactlog', 'add_sampledelivery', 'change_sampledelivery',
                'add_customer', 'change_customer', 'view_customer',
                'view_product', 'view_stockmovement',
            ],
            content_type__app_label__in=['orders', 'returns', 'crm', 'customers', 'core'],
        )
        salesperson.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(f'Salesperson: {perms.count()} permissions'))

        # Manager: full access (core, reports, dashboard, master_data)
        manager, _ = Group.objects.get_or_create(name='Manager')
        perms = Permission.objects.filter(
            codename__in=[
                'add_salesorder', 'change_salesorder', 'delete_salesorder', 'view_salesorder',
                'add_payment', 'view_payment',
                'add_returnrequest', 'change_returnrequest', 'delete_returnrequest', 'view_returnrequest',
                'add_lead', 'change_lead', 'delete_lead', 'view_lead',
                'add_contactlog', 'add_sampledelivery', 'change_sampledelivery',
                'add_customer', 'change_customer', 'delete_customer', 'view_customer',
                'add_purchaseorder', 'change_purchaseorder', 'delete_purchaseorder', 'view_purchaseorder',
                'add_expense', 'view_expense',
                'add_product', 'change_product', 'view_product', 'view_stockmovement',
                'change_companysetting',
                'view_auditlog',
            ],
            content_type__app_label__in=[
                'orders', 'returns', 'crm', 'customers', 'purchasing', 'accounting',
                'core', 'master_data', 'common',
            ],
        )
        manager.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(f'Manager: {perms.count()} permissions'))

        # Accountant: payments, expenses, view orders, reports
        accountant, _ = Group.objects.get_or_create(name='Accountant')
        perms = Permission.objects.filter(
            codename__in=[
                'add_payment', 'view_payment', 'view_salesorder',
                'add_expense', 'view_expense',
                'view_product', 'view_auditlog',
            ],
            content_type__app_label__in=['orders', 'accounting', 'core', 'common'],
        )
        accountant.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(f'Accountant: {perms.count()} permissions'))

        self.stdout.write(self.style.SUCCESS('Groups created/updated. Assign users via Admin → Users → Groups.'))
