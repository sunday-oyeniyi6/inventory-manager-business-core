from django.db import models
from django.conf import settings
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Taux de taxe par défaut en pourcentage (ex: 18.00 pour 18%)")
    
    # Keycloak fields
    keycloak_realm_name = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Nom du realm dans Keycloak")
    keycloak_client_id = models.CharField(max_length=255, blank=True, null=True, help_text="Client ID du backend dans le realm du tenant")
    encrypted_keycloak_client_secret = models.BinaryField(blank=True, null=True, help_text="Secret chiffré du client backend")
    
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

class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True, help_text="Ex: catalog:read, inventory:write")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.code

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Ex: STORE_MANAGER, TENANT_ADMIN")
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')

    def __str__(self):
        return self.name

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # UUID coming from Keycloak (the 'sub' claim)
    external_reference = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Keycloak UUID")
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, blank=True, null=True, related_name='users')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True, related_name='users')

    def __str__(self):
        return self.username or self.email or str(self.id)
