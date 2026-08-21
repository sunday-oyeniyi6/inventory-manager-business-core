from django.db import models
from django.conf import settings
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Taux de taxe par défaut en pourcentage (ex: 18.00 pour 18%)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Office(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='offices')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

class TenantManager(models.Manager):
    def get_queryset(self):
        # In a real implementation, this would filter by the tenant set in context/middleware
        # e.g., from core.middleware import get_current_tenant
        # current_tenant = get_current_tenant()
        # if current_tenant:
        #     return super().get_queryset().filter(tenant=current_tenant)
        return super().get_queryset()

class TenantScopedModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    objects = TenantManager()
    all_objects = models.Manager() # Bypass tenant isolation if needed (e.g. admin)

    class Meta:
        abstract = True
