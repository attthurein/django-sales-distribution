from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('backups/', views.backup_list, name='backup_list'),
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/restore/<str:filename>/', views.restore_backup, name='restore_backup'),
    path('backups/delete/<str:filename>/', views.delete_backup, name='delete_backup'),
    path('backups/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('backups/reset/', views.reset_data, name='reset_data'),
]
