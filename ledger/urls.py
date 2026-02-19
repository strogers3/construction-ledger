from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('entries/', views.entry_list, name='entry_list'),
    path('entries/new/', views.entry_create, name='entry_create'),
    path('entries/<int:pk>/', views.entry_detail, name='entry_detail'),
    path('entries/<int:pk>/edit/', views.entry_edit, name='entry_edit'),
    path('entries/<int:pk>/split/', views.entry_split, name='entry_split'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/new/', views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/rename/', views.supplier_rename, name='supplier_rename'),
]
