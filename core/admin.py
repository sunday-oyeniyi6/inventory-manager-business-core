from django.contrib import admin
from .models import Tenant, Office

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_tax_rate', 'created_at')
    search_fields = ('name',)

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'location')
    list_filter = ('tenant',)
    search_fields = ('name', 'location')
