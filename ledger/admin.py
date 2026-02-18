from django.contrib import admin
from .models import Supplier, TypeDescription, ConstructionEntry


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(TypeDescription)
class TypeDescriptionAdmin(admin.ModelAdmin):
    list_display = ['code', 'description']


@admin.register(ConstructionEntry)
class ConstructionEntryAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'description', 'stage', 'lc_stage', 'supplier',
        'cost', 'posted', 'lm', 'invoice_number',
    ]
    list_filter = ['posted', 'lm', 'delivery_type', 'type_description', 'supplier']
    search_fields = ['description', 'notes', 'invoice_number']
    date_hierarchy = 'date'
