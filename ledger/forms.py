from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

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


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text='Assign the user to one or more groups.',
    )
    is_staff = forms.BooleanField(required=False, label='Admin (staff access)')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'groups', 'is_staff']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.is_staff = self.cleaned_data.get('is_staff', False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('groups') or [])
        return user


class UserEditForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
    new_password1 = forms.CharField(
        required=False,
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        required=False,
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.all()

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 or p2:
            if p1 != p2:
                self.add_error('new_password2', "Passwords don't match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('new_password1'):
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('groups') or [])
        return user


# Ledger permissions presented with friendly labels, grouped by category.
# Each tuple is (codename, label, category).
LEDGER_PERMISSIONS = [
    # Entries
    ('view_constructionentry',   'View entries',           'Entries'),
    ('add_constructionentry',    'Add entries',            'Entries'),
    ('change_constructionentry', 'Edit entries',           'Entries'),
    ('delete_constructionentry', 'Delete entries',         'Entries'),
    # Suppliers
    ('view_supplier',            'View suppliers',         'Suppliers'),
    ('add_supplier',             'Add suppliers',          'Suppliers'),
    ('change_supplier',          'Edit / rename / merge suppliers', 'Suppliers'),
    ('delete_supplier',          'Delete suppliers',       'Suppliers'),
    # Type descriptions
    ('view_typedescription',     'View type descriptions', 'Type Descriptions'),
    ('change_typedescription',   'Edit type descriptions', 'Type Descriptions'),
]

LEDGER_PERMISSION_CHOICES = [(code, label) for code, label, _ in LEDGER_PERMISSIONS]


class GroupForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    permissions = forms.MultipleChoiceField(
        choices=LEDGER_PERMISSION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
