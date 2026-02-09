from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from datetime import datetime
from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm


@login_required
def expense_list(request):
    """List all expenses with filters"""
    category_filter = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    expenses = Expense.objects.select_related('category', 'recorded_by').all()
    
    if category_filter:
        expenses = expenses.filter(category_id=category_filter)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    
    total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pagination
    paginator = Paginator(expenses.order_by('-date'), 25)  # Show 25 expenses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': _('Expenses'),
        'expenses': page_obj,
        'categories': ExpenseCategory.objects.all(),
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total': total,
    }
    return render(request, 'accounting/expense_list.html', context)


@login_required
@permission_required('accounting.add_expense', raise_exception=True)
def expense_create(request):
    """Create new expense with form validation."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.recorded_by = request.user
                expense.save()
            messages.success(request, _('Expense recorded successfully'))
            return redirect('accounting:expense_list')
    else:
        form = ExpenseForm(initial={'date': datetime.now().date()})

    context = {
        'title': _('Record Expense'),
        'form': form,
    }
    return render(request, 'accounting/expense_create.html', context)


@login_required
def expense_summary(request):
    """Expense summary by category and month"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
    except (ValueError, TypeError):
        year = datetime.now().year

    # By category
    by_category = Expense.objects.filter(date__year=year).values(
        'category__name'
    ).annotate(total=Sum('amount')).order_by('-total')
    
    # By month
    by_month = Expense.objects.filter(date__year=year).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Sum('amount')).order_by('month')
    
    total_expenses = Expense.objects.filter(date__year=year).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    available_years = list(
        Expense.objects.values_list('date__year', flat=True)
        .distinct().order_by('-date__year')
    )
    if not available_years:
        available_years = [datetime.now().year]

    context = {
        'title': _('Expense Summary'),
        'year': year,
        'available_years': available_years,
        'by_category': by_category,
        'by_month': by_month,
        'total_expenses': total_expenses,
    }
    return render(request, 'accounting/expense_summary.html', context)


@login_required
def expense_category_list(request):
    """List all expense categories."""
    categories = ExpenseCategory.objects.all().order_by('name')
    return render(request, 'accounting/expense_category_list.html', {
        'title': _('Expense Categories'),
        'categories': categories
    })


@login_required
@permission_required('accounting.add_expensecategory', raise_exception=True)
def expense_category_create(request):
    """Create new expense category."""
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Expense category created successfully.'))
            return redirect('accounting:expense_category_list')
    else:
        form = ExpenseCategoryForm()

    return render(request, 'accounting/expense_category_form.html', {
        'title': _('Create Expense Category'),
        'form': form
    })


@login_required
@permission_required('accounting.change_expensecategory', raise_exception=True)
def expense_category_update(request, pk):
    """Update expense category."""
    category = ExpenseCategory.objects.get(pk=pk)
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Expense category updated successfully.'))
            return redirect('accounting:expense_category_list')
    else:
        form = ExpenseCategoryForm(instance=category)

    return render(request, 'accounting/expense_category_form.html', {
        'title': _('Edit Expense Category'),
        'form': form
    })


@login_required
@permission_required('accounting.delete_expensecategory', raise_exception=True)
def expense_category_delete(request, pk):
    """Delete expense category."""
    category = ExpenseCategory.objects.get(pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, _('Expense category deleted successfully.'))
        except Exception as e:
            messages.error(request, _('Cannot delete category: it may be in use.'))
        return redirect('accounting:expense_category_list')
    
    return render(request, 'accounting/expense_category_confirm_delete.html', {
        'title': _('Delete Expense Category'),
        'category': category
    })
