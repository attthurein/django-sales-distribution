"""
Master Data URL configuration.
"""
from django.urls import path
from . import views

app_name = 'master_data'

urlpatterns = [
    path('company-setting/', views.company_setting, name='company_setting'),
]
