from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/summary/', views.expense_summary, name='expense_summary'),
    
    # Expense Categories
    path('categories/', views.expense_category_list, name='expense_category_list'),
    path('categories/create/', views.expense_category_create, name='expense_category_create'),
    path('categories/<int:pk>/edit/', views.expense_category_update, name='expense_category_update'),
    path('categories/<int:pk>/delete/', views.expense_category_delete, name='expense_category_delete'),
]
