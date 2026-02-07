from django.test import TestCase
from django.contrib.auth.models import User
from common.audit import set_current_user
from common.models import AuditLog
from customers.models import Customer
from master_data.models import CustomerType

class AuditLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.customer_type = CustomerType.objects.create(name_en='Retail', code='RET')
        # Simulate middleware setting user
        set_current_user(self.user)

    def tearDown(self):
        set_current_user(None)

    def test_audit_log_creation(self):
        # 1. Test Create
        customer = Customer.objects.create(
            name='Test Customer',
            phone='09123456789',
            customer_type=self.customer_type
        )
        
        # Check if log exists
        log = AuditLog.objects.filter(
            model_name='customers.customer',
            object_id=customer.id,
            action='create'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertIn('Test Customer', log.changes['summary'])

        # 2. Test Update
        customer.name = 'Updated Customer'
        customer.save()
        
        log = AuditLog.objects.filter(
            model_name='customers.customer',
            object_id=customer.id,
            action='update'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.changes['diff']['name']['old'], 'Test Customer')
        self.assertEqual(log.changes['diff']['name']['new'], 'Updated Customer')

        # 3. Test Delete (Soft Delete actually updates deleted_at, so it might be an update or custom logic?)
        # Since Customer now uses SoftDeleteMixin, .delete() triggers soft_delete() which calls save().
        # So it should be an UPDATE action on deleted_at field.
        # But wait, SoftDeleteMixin.soft_delete() calls self.save(update_fields=['deleted_at']).
        
        customer.delete() # Triggers soft delete
        
        log = AuditLog.objects.filter(
            model_name='customers.customer',
            object_id=customer.id,
            action='update'
        ).order_by('-created_at').first()
        
        self.assertIsNotNone(log)
        self.assertIn('deleted_at', log.changes['diff'])
