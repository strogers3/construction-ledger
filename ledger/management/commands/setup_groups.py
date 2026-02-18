from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from ledger.models import ConstructionEntry, Supplier, TypeDescription


class Command(BaseCommand):
    help = 'Create Viewer and Editor permission groups'

    def handle(self, *args, **options):
        # Content types
        entry_ct = ContentType.objects.get_for_model(ConstructionEntry)
        supplier_ct = ContentType.objects.get_for_model(Supplier)
        type_ct = ContentType.objects.get_for_model(TypeDescription)

        # View permissions
        view_perms = Permission.objects.filter(
            codename__startswith='view_',
            content_type__in=[entry_ct, supplier_ct, type_ct],
        )

        # Edit permissions (change + add + delete for entries/suppliers)
        edit_perms = Permission.objects.filter(
            content_type__in=[entry_ct, supplier_ct, type_ct],
            codename__in=[
                'change_constructionentry',
                'add_constructionentry',
                'delete_constructionentry',
                'change_supplier',
                'add_supplier',
                'delete_supplier',
                'change_typedescription',
            ],
        )

        # Viewer group
        viewer, created = Group.objects.get_or_create(name='Viewer')
        viewer.permissions.set(view_perms)
        status = 'Created' if created else 'Updated'
        self.stdout.write(f'{status} Viewer group with {viewer.permissions.count()} permissions')

        # Editor group
        editor, created = Group.objects.get_or_create(name='Editor')
        editor.permissions.set(view_perms | edit_perms)
        status = 'Created' if created else 'Updated'
        self.stdout.write(f'{status} Editor group with {editor.permissions.count()} permissions')

        self.stdout.write(self.style.SUCCESS('Permission groups ready.'))
