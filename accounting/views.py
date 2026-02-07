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
from .forms import ExpenseForm


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
