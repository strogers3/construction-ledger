from django import forms
from .models import ConstructionEntry


class ConstructionEntryForm(forms.ModelForm):
    class Meta:
        model = ConstructionEntry
        fields = [
            'date', 'description', 'stage', 'lc_stage', 'supplier',
            'estimate', 'qty', 'supplies_cost', 'tax_fees', 'cost',
            'invoiced_amt', 'posted', 'lm', 'supervisor', 'invoice_number',
            'delivery_type', 'materials', 'book_number', 'notes',
            'type_description',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'stage': forms.TextInput(attrs={'class': 'form-control'}),
            'lc_stage': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'estimate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplies_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'invoiced_amt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'posted': forms.Select(attrs={'class': 'form-select'}),
            'lm': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_type': forms.Select(attrs={'class': 'form-select'}),
            'materials': forms.TextInput(attrs={'class': 'form-control'}),
            'book_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_description': forms.Select(attrs={'class': 'form-select'}),
        }
