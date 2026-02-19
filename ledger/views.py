from decimal import Decimal, ROUND_HALF_UP

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q, Min, Max
from django.core.paginator import Paginator
from django.forms import formset_factory
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied

from .models import ConstructionEntry, Supplier, TypeDescription, EntryChangeLog
from django.contrib import messages

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .forms import ConstructionEntryForm, UserCreateForm, UserEditForm, GroupForm, LEDGER_PERMISSIONS


@login_required
def dashboard(request):
    entries = ConstructionEntry.objects.all()
    total_entries = entries.count()
    total_cost = entries.exclude(lm='X').aggregate(total=Sum('cost'))['total'] or 0
    total_transfers = entries.filter(lm='X').aggregate(total=Sum('cost'))['total'] or 0
    total_suppliers = Supplier.objects.count()
    date_range = entries.aggregate(min_date=Min('date'), max_date=Max('date'))

    # Cost by TypeDescription
    type_costs = (
        entries.filter(type_description__isnull=False).exclude(lm='X')
        .values('type_description_id', 'type_description__code', 'type_description__description')
        .annotate(total=Sum('cost'))
        .order_by('type_description__code')
    )
    type_labels = [f"{t['type_description__code']} - {t['type_description__description']}" for t in type_costs]
    type_values = [float(t['total'] or 0) for t in type_costs]
    type_ids = [t['type_description_id'] for t in type_costs]

    # Cost by L/M category
    lm_costs = (
        entries.filter(lm__in=['L', 'M', 'U'])
        .values('lm')
        .annotate(total=Sum('cost'))
        .order_by('lm')
    )
    lm_map = {'L': 'Labor', 'M': 'Materials', 'U': 'Utility'}
    lm_labels = [lm_map.get(c['lm'], c['lm']) for c in lm_costs]
    lm_values = [float(c['total'] or 0) for c in lm_costs]
    lm_codes = [c['lm'] for c in lm_costs]

    # Transfers by Supplier
    transfer_costs = (
        entries.filter(lm='X', supplier__isnull=False)
        .values('supplier_id', 'supplier__name')
        .annotate(total=Sum('cost'))
        .order_by('-total')
    )
    transfer_labels = [t['supplier__name'] for t in transfer_costs]
    transfer_values = [float(t['total'] or 0) for t in transfer_costs]
    transfer_ids = [t['supplier_id'] for t in transfer_costs]

    # Cost by Supplier (excluding transfers)
    supplier_costs = (
        entries.filter(supplier__isnull=False).exclude(lm='X')
        .values('supplier_id', 'supplier__name')
        .annotate(total=Sum('cost'))
        .order_by('-total')
    )
    supplier_labels = [s['supplier__name'] for s in supplier_costs]
    supplier_values = [float(s['total'] or 0) for s in supplier_costs]
    supplier_ids = [s['supplier_id'] for s in supplier_costs]

    # Recent entries
    recent_entries = entries.select_related('supplier', 'type_description').order_by('-date', '-id')[:10]

    context = {
        'total_entries': total_entries,
        'total_cost': total_cost,
        'total_transfers': total_transfers,
        'total_suppliers': total_suppliers,
        'date_range': date_range,
        'type_labels': type_labels,
        'type_values': type_values,
        'type_ids': type_ids,
        'lm_labels': lm_labels,
        'lm_values': lm_values,
        'lm_codes': lm_codes,
        'transfer_labels': transfer_labels,
        'transfer_values': transfer_values,
        'transfer_ids': transfer_ids,
        'supplier_labels': supplier_labels,
        'supplier_values': supplier_values,
        'supplier_ids': supplier_ids,
        'recent_entries': recent_entries,
    }
    return render(request, 'ledger/dashboard.html', context)


@login_required
def entry_list(request):
    entries = ConstructionEntry.objects.select_related('supplier', 'type_description').all()

    # Filtering
    supplier_id = request.GET.get('supplier')
    type_id = request.GET.get('type')
    lm = request.GET.get('lm')
    posted = request.GET.get('posted')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search', '').strip()

    if supplier_id:
        entries = entries.filter(supplier_id=supplier_id)
    if type_id:
        entries = entries.filter(type_description_id=type_id)
    if lm:
        entries = entries.filter(lm=lm)
    if posted:
        entries = entries.filter(posted=posted)
    if date_from:
        entries = entries.filter(date__gte=date_from)
    if date_to:
        entries = entries.filter(date__lte=date_to)
    if search:
        entries = entries.filter(
            Q(description__icontains=search) |
            Q(notes__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    # Sorting
    sort = request.GET.get('sort', 'date')
    direction = request.GET.get('dir', 'asc')
    valid_sorts = ['date', 'description', 'supplier__name', 'cost', 'lm', 'type_description__code']
    if sort not in valid_sorts:
        sort = 'date'
    order_prefix = '-' if direction == 'desc' else ''
    entries = entries.order_by(f'{order_prefix}{sort}', 'id')

    # Pagination
    paginator = Paginator(entries, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Totals & L/M subtotals (on filtered queryset, before pagination)
    totals = entries.aggregate(total_cost=Sum('cost'), entry_count=Count('id'))
    lm_map = {'L': 'Labor', 'M': 'Materials', 'U': 'Utility', 'X': 'Transfer'}
    lm_subtotals = (
        entries.filter(lm__in=['L', 'M', 'U', 'X'])
        .values('lm')
        .annotate(total=Sum('cost'), count=Count('id'))
        .order_by('lm')
    )
    lm_subtotals = [
        {'code': s['lm'], 'label': lm_map.get(s['lm'], s['lm']), 'total': s['total'], 'count': s['count']}
        for s in lm_subtotals
    ]

    # Filter options
    suppliers = Supplier.objects.order_by('name')
    types = TypeDescription.objects.order_by('code')

    context = {
        'page_obj': page_obj,
        'suppliers': suppliers,
        'types': types,
        'totals': totals,
        'lm_subtotals': lm_subtotals,
        'current_filters': {
            'supplier': supplier_id or '',
            'type': type_id or '',
            'lm': lm or '',
            'posted': posted or '',
            'date_from': date_from or '',
            'date_to': date_to or '',
            'search': search,
            'sort': sort,
            'dir': direction,
        },
        'total_filtered': paginator.count,
    }
    return render(request, 'ledger/entry_list.html', context)


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(
        ConstructionEntry.objects.select_related('supplier', 'type_description'),
        pk=pk
    )
    change_logs = entry.change_logs.select_related('user').order_by('-timestamp')
    return render(request, 'ledger/entry_detail.html', {'entry': entry, 'change_logs': change_logs})


@login_required
def supplier_list(request):
    suppliers = (
        Supplier.objects.annotate(
            entry_count=Count('constructionentry'),
            total_cost=Sum('constructionentry__cost'),
        )
    )

    sort = request.GET.get('sort', 'name')
    direction = request.GET.get('dir', 'asc')
    valid_sorts = ['name', 'entry_count', 'total_cost']
    if sort not in valid_sorts:
        sort = 'name'
    order_prefix = '-' if direction == 'desc' else ''
    suppliers = suppliers.order_by(f'{order_prefix}{sort}')

    return render(request, 'ledger/supplier_list.html', {
        'suppliers': suppliers,
        'current_sort': sort,
        'current_dir': direction,
    })


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    entries = (
        ConstructionEntry.objects
        .filter(supplier=supplier)
        .select_related('type_description')
    )
    totals = entries.aggregate(
        total_cost=Sum('cost'),
        entry_count=Count('id'),
    )

    lm_map = {'L': 'Labor', 'M': 'Materials', 'U': 'Utility', 'X': 'Transfer'}
    lm_subtotals = (
        entries.filter(lm__in=['L', 'M', 'U', 'X'])
        .values('lm')
        .annotate(total=Sum('cost'), count=Count('id'))
        .order_by('lm')
    )
    lm_subtotals = [
        {'code': s['lm'], 'label': lm_map.get(s['lm'], s['lm']), 'total': s['total'], 'count': s['count']}
        for s in lm_subtotals
    ]

    sort = request.GET.get('sort', 'date')
    direction = request.GET.get('dir', 'desc')
    valid_sorts = ['date', 'description', 'type_description__code', 'lm', 'cost', 'posted']
    if sort not in valid_sorts:
        sort = 'date'
    order_prefix = '-' if direction == 'desc' else ''
    entries = entries.order_by(f'{order_prefix}{sort}', 'id')

    return render(request, 'ledger/supplier_detail.html', {
        'supplier': supplier,
        'entries': entries,
        'totals': totals,
        'lm_subtotals': lm_subtotals,
        'current_sort': sort,
        'current_dir': direction,
    })


@login_required
@permission_required('ledger.change_constructionentry', raise_exception=True)
def entry_edit(request, pk):
    entry = get_object_or_404(ConstructionEntry, pk=pk)
    if request.method == 'POST':
        old_values = {
            f: str(getattr(entry, f)) if getattr(entry, f) is not None else ''
            for f in ConstructionEntryForm.Meta.fields
        }
        form = ConstructionEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            changes = {
                f: {'old': old_values[f], 'new': str(getattr(entry, f)) if getattr(entry, f) is not None else ''}
                for f in ConstructionEntryForm.Meta.fields
                if (str(getattr(entry, f)) if getattr(entry, f) is not None else '') != old_values[f]
            }
            if changes:
                _log_entry_change(entry, request.user, 'edit', changes)
            return redirect('ledger:entry_detail', pk=entry.pk)
    else:
        form = ConstructionEntryForm(instance=entry)
    return render(request, 'ledger/entry_edit.html', {'form': form, 'entry': entry})


@login_required
@permission_required('ledger.add_constructionentry', raise_exception=True)
def entry_create(request):
    if request.method == 'POST':
        form = ConstructionEntryForm(request.POST)
        if form.is_valid():
            entry = form.save()
            _log_entry_change(entry, request.user, 'create')
            return redirect('ledger:entry_detail', pk=entry.pk)
    else:
        form = ConstructionEntryForm()
    return render(request, 'ledger/entry_create.html', {'form': form})


def _log_entry_change(entry, user, action, changes=None, notes=''):
    """Record a create/edit/split action on a ConstructionEntry."""
    EntryChangeLog.objects.create(
        entry=entry,
        entry_id_snapshot=entry.pk if entry else None,
        user=user,
        action=action,
        changes=changes or {},
        notes=notes,
    )


def _divide_amount(amount, n):
    """Divide a decimal amount into n parts, putting any remainder on the first."""
    if amount is None:
        return [None] * n
    amount = Decimal(str(amount))
    base = (amount / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    parts = [base] * n
    remainder = amount - base * n
    parts[0] += remainder
    return parts


@login_required
@permission_required('ledger.change_constructionentry', raise_exception=True)
def entry_split(request, pk):
    entry = get_object_or_404(
        ConstructionEntry.objects.select_related('supplier', 'type_description'),
        pk=pk,
    )
    money_fields = ['cost', 'supplies_cost', 'tax_fees', 'invoiced_amt', 'estimate']

    if request.method == 'POST':
        num_splits = int(request.POST.get('num_splits', 2))
        SplitFormSet = formset_factory(ConstructionEntryForm, extra=0)
        formset = SplitFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                form.save()
            _log_entry_change(entry, request.user, 'split', notes=f"Split into {num_splits} parts")
            entry.delete()
            return redirect('ledger:entry_list')
        return render(request, 'ledger/entry_split.html', {
            'entry': entry,
            'formset': formset,
            'num_splits': num_splits,
        })

    # GET — build initial data with divided monetary fields
    num_splits = int(request.GET.get('n', 2))
    if num_splits < 2:
        num_splits = 2

    base_data = {}
    for field in ConstructionEntryForm.Meta.fields:
        val = getattr(entry, field)
        if field == 'supplier':
            base_data['supplier'] = entry.supplier_id
        elif field == 'type_description':
            base_data['type_description'] = entry.type_description_id
        elif field == 'date':
            base_data['date'] = val.isoformat() if val else ''
        else:
            base_data[field] = val if val is not None else ''

    divided = {f: _divide_amount(getattr(entry, f), num_splits) for f in money_fields}

    initial = []
    for i in range(num_splits):
        row = dict(base_data)
        for f in money_fields:
            row[f] = divided[f][i] if divided[f][i] is not None else ''
        initial.append(row)

    SplitFormSet = formset_factory(ConstructionEntryForm, extra=0)
    formset = SplitFormSet(initial=initial)

    return render(request, 'ledger/entry_split.html', {
        'entry': entry,
        'formset': formset,
        'num_splits': num_splits,
    })


@login_required
@permission_required('ledger.change_supplier', raise_exception=True)
def supplier_rename(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        new_name = request.POST.get('new_name', '').strip()
        confirm = request.POST.get('confirm_override') == '1'

        if not new_name:
            messages.error(request, 'Supplier name cannot be empty.')
            return redirect('ledger:supplier_detail', pk=pk)

        existing = Supplier.objects.filter(name=new_name).exclude(pk=pk).first()

        if existing and not confirm:
            # Show warning — supplier with that name already exists
            return render(request, 'ledger/supplier_rename_confirm.html', {
                'supplier': supplier,
                'new_name': new_name,
                'existing': existing,
            })

        if existing and confirm:
            # Merge: reassign all entries to existing supplier, delete this one
            ConstructionEntry.objects.filter(supplier=supplier).update(supplier=existing)
            supplier.delete()
            messages.success(request, f'Merged "{supplier.name}" into "{existing.name}". All entries reassigned.')
            return redirect('ledger:supplier_detail', pk=existing.pk)

        # No conflict — just rename
        old_name = supplier.name
        supplier.name = new_name
        supplier.save()
        messages.success(request, f'Supplier renamed from "{old_name}" to "{new_name}".')
        return redirect('ledger:supplier_detail', pk=supplier.pk)

    return redirect('ledger:supplier_detail', pk=pk)


@login_required
def audit_log(request):
    logs = EntryChangeLog.objects.select_related('entry', 'user').order_by('-timestamp')
    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'ledger/audit_log.html', {'page_obj': page_obj})


@login_required
def user_list(request):
    if not request.user.is_staff:
        raise PermissionDenied
    users = get_user_model().objects.prefetch_related('groups').order_by('username')
    return render(request, 'ledger/user_list.html', {'users': users})


@login_required
def user_create(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{form.cleaned_data["username"]}" created successfully.')
            return redirect('ledger:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'ledger/user_create.html', {'form': form})


@login_required
def user_edit(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    User = get_user_model()
    edited_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=edited_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{edited_user.username}" updated successfully.')
            return redirect('ledger:user_list')
    else:
        form = UserEditForm(instance=edited_user)
    return render(request, 'ledger/user_edit.html', {'form': form, 'edited_user': edited_user})


def _group_form_initial(group):
    """Return initial permission codenames for a group, filtered to ledger permissions."""
    known = {code for code, _, _ in LEDGER_PERMISSIONS}
    return list(
        group.permissions
        .filter(content_type__app_label='ledger')
        .values_list('codename', flat=True)
        .filter(codename__in=known)
    )


def _perm_categories(checked_codes):
    """Return LEDGER_PERMISSIONS grouped by category with checked state for the template."""
    from itertools import groupby
    result = []
    for category, perms in groupby(LEDGER_PERMISSIONS, key=lambda x: x[2]):
        result.append({
            'category': category,
            'perms': [
                {'code': code, 'label': label, 'checked': code in checked_codes}
                for code, label, _ in perms
            ],
        })
    return result


def _save_group_permissions(group, codenames):
    """Set a group's permissions to the given ledger codenames."""
    perms = Permission.objects.filter(
        codename__in=codenames,
        content_type__app_label='ledger',
    )
    group.permissions.set(perms)


@login_required
def group_list(request):
    if not request.user.is_staff:
        raise PermissionDenied
    groups = Group.objects.prefetch_related('permissions').annotate(
        member_count=Count('user')
    ).order_by('name')
    known_codes = {code for code, _, _ in LEDGER_PERMISSIONS}
    perm_labels = {code: label for code, label, _ in LEDGER_PERMISSIONS}
    group_data = []
    for g in groups:
        active = [
            perm_labels[p.codename]
            for p in g.permissions.all()
            if p.codename in known_codes
        ]
        group_data.append({'group': g, 'active_perms': active})
    return render(request, 'ledger/group_list.html', {'group_data': group_data})


@login_required
def group_create(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Group.objects.filter(name=name).exists():
                form.add_error('name', 'A group with this name already exists.')
            else:
                group = Group.objects.create(name=name)
                _save_group_permissions(group, form.cleaned_data.get('permissions', []))
                messages.success(request, f'Group "{name}" created.')
                return redirect('ledger:group_list')
        checked = set(request.POST.getlist('permissions'))
    else:
        form = GroupForm()
        checked = set()
    return render(request, 'ledger/group_edit.html', {
        'form': form,
        'perm_categories': _perm_categories(checked),
        'is_create': True,
    })


@login_required
def group_edit(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        if 'delete' in request.POST:
            name = group.name
            group.delete()
            messages.success(request, f'Group "{name}" deleted.')
            return redirect('ledger:group_list')
        form = GroupForm(request.POST)
        if form.is_valid():
            new_name = form.cleaned_data['name']
            if Group.objects.filter(name=new_name).exclude(pk=pk).exists():
                form.add_error('name', 'A group with this name already exists.')
            else:
                group.name = new_name
                group.save()
                _save_group_permissions(group, form.cleaned_data.get('permissions', []))
                messages.success(request, f'Group "{group.name}" updated.')
                return redirect('ledger:group_list')
        checked = set(request.POST.getlist('permissions'))
    else:
        checked = set(_group_form_initial(group))
        form = GroupForm(initial={
            'name': group.name,
            'permissions': list(checked),
        })
    return render(request, 'ledger/group_edit.html', {
        'form': form,
        'group': group,
        'perm_categories': _perm_categories(checked),
        'is_create': False,
    })
