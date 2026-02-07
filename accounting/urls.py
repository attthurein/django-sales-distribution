from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/summary/', views.expense_summary, name='expense_summary'),
]
