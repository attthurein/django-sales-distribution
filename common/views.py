import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.http import HttpResponse, Http404
from django.utils.translation import gettext as _
from pathlib import Path
from datetime import datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.apps import apps
from django.db import transaction
from common.utils import reset_model_sequences

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def backup_list(request):
    backup_dir = settings.BASE_DIR / 'backups'
    if not backup_dir.exists():
        backup_dir.mkdir(exist_ok=True)
    
    if request.method == 'POST' and 'upload_backup' in request.FILES:
        backup_file = request.FILES['upload_backup']
        if not backup_file.name.endswith('.json'):
            messages.error(request, _('Invalid file format. Please upload a .json file.'))
        else:
            file_path = backup_dir / backup_file.name
            with open(file_path, 'wb+') as destination:
                for chunk in backup_file.chunks():
                    destination.write(chunk)
            messages.success(request, _('Backup uploaded successfully.'))
            return redirect('common:backup_list')

    backups = []
    for f in backup_dir.glob('backup_*.json'):
        try:
            stat = f.stat()
            backups.append({
                'name': f.name,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_mtime),
                'path': str(f)
            })
        except OSError:
            pass
    
    backups.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, 'common/backup_list.html', {'backups': backups})

@user_passes_test(is_superuser)
def create_backup(request):
    if request.method == 'POST':
        try:
            call_command('backup_db')
            messages.success(request, _('Backup created successfully.'))
        except Exception as e:
            messages.error(request, _('Error creating backup: %(error)s') % {'error': str(e)})
    return redirect('common:backup_list')

@user_passes_test(is_superuser)
def restore_backup(request, filename):
    if request.method == 'POST':
        backup_file = settings.BASE_DIR / 'backups' / filename
        if not backup_file.exists():
            messages.error(request, _('Backup file not found.'))
        else:
            try:
                # Warning: This adds data, it doesn't replace the whole DB unless flushed.
                # For safety in this context, we just loaddata.
                call_command('loaddata', str(backup_file))
                messages.success(request, _('Database restored successfully.'))
            except Exception as e:
                messages.error(request, _('Error restoring database: %(error)s') % {'error': str(e)})
    return redirect('common:backup_list')

@user_passes_test(is_superuser)
def delete_backup(request, filename):
    if request.method == 'POST':
        backup_file = settings.BASE_DIR / 'backups' / filename
        if backup_file.exists():
            try:
                backup_file.unlink()
                messages.success(request, _('Backup deleted successfully.'))
            except Exception as e:
                messages.error(request, _('Error deleting backup: %(error)s') % {'error': str(e)})
        else:
             messages.error(request, _('Backup file not found.'))
    return redirect('common:backup_list')

@user_passes_test(is_superuser)
def download_backup(request, filename):
    backup_file = settings.BASE_DIR / 'backups' / filename
    if backup_file.exists():
        with open(backup_file, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/json")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(backup_file)
            return response
    raise Http404

@user_passes_test(is_superuser)
def reset_data(request):
    if request.method == 'POST':
        reset_type = request.POST.get('reset_type')
        
        # Transactional Data (User Input)
        transactional_models = [
            'orders.SalesOrder', 'orders.OrderItem', 'orders.Payment', 'orders.Invoice',
            'purchasing.PurchaseOrder', 'purchasing.PurchaseOrderItem', 'purchasing.PurchaseReceipt',
            'returns.ReturnRequest', 'returns.ReturnItem',
            'accounting.Expense',
            'crm.Lead', 'crm.ContactLog', 'crm.SampleDelivery',
            'core.StockMovement', 'core.StockAdjustment', 'core.Batch',
            'reports.DailySalesSummary', 'reports.DailyPaymentSummary', 'reports.DailyExpenseSummary'
        ]
        
        # Master Data
        master_data_models = [
            'core.Product', 'core.ProductCategory', 'core.ProductPriceTier', 'core.Brand', 'core.UnitOfMeasure',
            'customers.Customer', 'customers.SalesPerson',
            'master_data.Region', 'master_data.Township', 'master_data.DeliveryRoute', 'master_data.Promotion'
        ]

        try:
            with transaction.atomic():
                deleted_models = []
                # 1. Always delete transactional data first (to avoid ProtectedError)
                for model_string in transactional_models:
                    try:
                        app_label, model_name = model_string.split('.')
                        Model = apps.get_model(app_label, model_name)
                        # Use _base_manager to ensure we get all objects even if soft-deleted ones exist and interfere
                        Model._base_manager.all().delete()
                        deleted_models.append(Model)
                    except LookupError:
                        pass # Model might not exist in this project version
                    except Exception as e:
                        print(f"Error deleting {model_string}: {e}")

                # 2. If 'all' selected, delete master data
                if reset_type == 'all':
                    for model_string in master_data_models:
                        try:
                            app_label, model_name = model_string.split('.')
                            Model = apps.get_model(app_label, model_name)
                            Model._base_manager.all().delete()
                            deleted_models.append(Model)
                        except LookupError:
                            pass
                        except Exception as e:
                             print(f"Error deleting {model_string}: {e}")
                    
                    messages.success(request, _('All data (Master + Transactions) has been reset successfully.'))
                else:
                    messages.success(request, _('Transactional data (User Input) has been reset successfully.'))
                
                # Reset sequences
                reset_model_sequences(deleted_models)
                    
        except Exception as e:
            messages.error(request, _('Error resetting data: %(error)s') % {'error': str(e)})
            
    return redirect('common:backup_list')
