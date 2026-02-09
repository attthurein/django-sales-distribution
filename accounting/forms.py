"""
Accounting forms - Expense with validation.
"""
from django import forms
from .models import Expense, ExpenseCategory


class ExpenseCategoryForm(forms.ModelForm):
    """Form for expense categories."""
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class ExpenseForm(forms.ModelForm):
    """Expense form with validation."""

    class Meta:
        model = Expense
        fields = ['date', 'category', 'amount', 'description', 'paid_to']
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'paid_to': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
