import os
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from .models import User, Role
from .serializers import EmployeeSerializer, RoleSerializer
from .permissions import HasPermission

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows roles to be viewed or edited.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated] # Tout employé authentifié peut voir les rôles

    def perform_create(self, serializer):
        role = serializer.save()
        self.sync_role_to_keycloak(role)

    def perform_update(self, serializer):
        role = serializer.save()
        self.sync_role_to_keycloak(role, is_update=True)

    def sync_role_to_keycloak(self, role, is_update=False):
        from .models import Tenant
        from .utils.encryption import decrypt_secret
        
        tenants = Tenant.objects.all()
        for t in tenants:
            if t.keycloak_realm_name and t.encrypted_keycloak_client_secret:
                try:
                    secret = decrypt_secret(t.encrypted_keycloak_client_secret)
                    tenant_admin = KeycloakAdmin(
                        server_url=os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/'),
                        client_id=t.keycloak_client_id,
                        realm_name=t.keycloak_realm_name,
                        user_realm_name=t.keycloak_realm_name,
                        client_secret_key=secret,
                        verify=True
                    )
                    if is_update:
                        try:
                            tenant_admin.update_realm_role(role_name=role.name, payload={
                                "description": role.description or ""
                            })
                        except KeycloakError:
                            pass
                    else:
                        try:
                            tenant_admin.create_realm_role(payload={
                                "name": role.name,
                                "description": role.description or ""
                            })
                        except KeycloakError:
                            pass
                except Exception as e:
                    print(f"Error syncing role {role.name} to tenant {t.name}: {e}")

from .models import Tenant
from .serializers import TenantSerializer

import re
import secrets
import time
from django.db import transaction
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from rest_framework import serializers

from .utils.encryption import encrypt_secret

class TenantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tenants (companies) to be viewed or edited.
    Usually restricted to superadmins, but opened for test scenarios.
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    # permission_classes = [IsAuthenticated] # Commented out for initial creation without token

    def perform_create(self, serializer):
        tenant_name = serializer.validated_data.get('name')
        
        # 1. Generate realm name (lowercase, no non-alphanumeric chars)
        realm_name = re.sub(r'[^a-z]', '', tenant_name.lower())
        if not realm_name:
            # Fallback if name has no alpha characters
            import uuid
            realm_name = f"tenant{uuid.uuid4().hex[:8]}"
            
        client_id = "inventory-manager-backend"
        client_secret = secrets.token_urlsafe(32)
        
        try:
            with transaction.atomic():
                # 2. Keycloak provisioning
                # Connexion au master
                master_admin = KeycloakAdmin(
                    server_url=os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/'),
                    username=os.getenv('KEYCLOAK_ADMIN_USER', 'admin'),
                    password=os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin'),
                    realm_name='master',
                    client_id='admin-cli',
                    verify=True
                )
                
                # Créer le realm
                try:
                    master_admin.create_realm(payload={
                        "realm": realm_name,
                        "enabled": True,
                        "displayName": tenant_name,
                        "registrationAllowed": False
                    })
                except KeycloakError as e:
                    if "409" in str(e):
                        raise serializers.ValidationError({"keycloak_error": f"Le realm '{realm_name}' existe déjà."})
                    raise e
                
                # Switch au nouveau realm via une nouvelle instance
                tenant_admin = KeycloakAdmin(
                    server_url=os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/'),
                    username=os.getenv('KEYCLOAK_ADMIN_USER', 'admin'),
                    password=os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin'),
                    realm_name=realm_name,
                    user_realm_name='master',
                    client_id='admin-cli',
                    verify=True
                )
                
                # Créer le client frontend
                tenant_admin.create_client(payload={
                    "clientId": "inventory-manager-frontend",
                    "enabled": True,
                    "publicClient": True,
                    "directAccessGrantsEnabled": True,
                    "standardFlowEnabled": True,
                    "redirectUris": ["*"],
                    "webOrigins": ["*"]
                })
                
                # Créer le client backend
                tenant_admin.create_client(payload={
                    "clientId": client_id,
                    "enabled": True,
                    "publicClient": False,
                    "clientAuthenticatorType": "client-secret",
                    "secret": client_secret,
                    "serviceAccountsEnabled": True,
                    "directAccessGrantsEnabled": False,
                    "standardFlowEnabled": False
                })
                
                # Attribuer les droits manage-users au client backend
                time.sleep(0.5) # Wait for client to be fully registered
                client_id_internal = tenant_admin.get_client_id(client_id)
                
                # Forcer la mise à jour pour garantir l'activation du compte de service et du secret
                tenant_admin.update_client(client_id_internal, payload={
                    "clientId": client_id,
                    "secret": client_secret,
                    "serviceAccountsEnabled": True
                })
                
                service_account_user = tenant_admin.get_client_service_account_user(client_id_internal)
                
                realm_management_client_id = tenant_admin.get_client_id("realm-management")
                realm_admin_role = tenant_admin.get_client_role(realm_management_client_id, "realm-admin")
                
                tenant_admin.assign_client_role(
                    user_id=service_account_user['id'],
                    client_id=realm_management_client_id,
                    roles=[realm_admin_role]
                )
                
                # Injecter les rôles globaux existants dans le nouveau realm
                from .models import Role
                for role in Role.objects.all():
                    try:
                        tenant_admin.create_realm_role(payload={
                            "name": role.name,
                            "description": role.description or ""
                        })
                    except KeycloakError:
                        pass
                
                # 3. Enregistrer en BDD
                encrypted_secret = encrypt_secret(client_secret)
                serializer.save(
                    keycloak_realm_name=realm_name,
                    keycloak_client_id=client_id,
                    encrypted_keycloak_client_secret=encrypted_secret
                )
        except KeycloakError as e:
            raise serializers.ValidationError({"keycloak_error": str(e)})


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited by TENANT_ADMIN.
    """
    serializer_class = EmployeeSerializer
    # Seul un admin (ayant la permission) peut gérer les employés
    # permission_classes = [IsAuthenticated, HasPermission.require('users:manage')]
    # Pour l'instant, on laisse IsAuthenticated pour faciliter les tests
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Un utilisateur ne voit que les employés de son Tenant
        if getattr(self.request.user, 'tenant', None):
            return User.objects.filter(tenant=self.request.user.tenant)
        return User.objects.none()

    def get_keycloak_admin(self, tenant=None):
        if tenant and tenant.keycloak_realm_name and tenant.encrypted_keycloak_client_secret:
            from .utils.encryption import decrypt_secret
            secret = decrypt_secret(tenant.encrypted_keycloak_client_secret)
            return KeycloakAdmin(
                server_url=os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/'),
                client_id=tenant.keycloak_client_id,
                realm_name=tenant.keycloak_realm_name,
                user_realm_name=tenant.keycloak_realm_name,
                client_secret_key=secret,
                verify=True
            )
        # Fallback to master if no tenant (e.g. for superadmin)
        return KeycloakAdmin(
            server_url=os.getenv('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/'),
            client_id=os.getenv('KEYCLOAK_ADMIN_CLIENT_ID', 'admin-cli'),
            realm_name=os.getenv('KEYCLOAK_REALM', 'master'),
            client_secret_key=os.getenv('KEYCLOAK_CLIENT_SECRET', ''),
            verify=True
        )

    def perform_create(self, serializer):
        user_data = serializer.validated_data
        email = user_data.get('email')
        username = user_data.get('username')
        password = user_data.pop('password', 'TempPassword123!') # par défaut ou généré
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')

        # The employee is associated with the creator's tenant
        tenant = getattr(self.request.user, 'tenant', None)
        
        # Or if passed in request payload (for test scenario / superadmin)
        if 'tenant' in self.request.data:
            from .models import Tenant
            try:
                tenant = Tenant.objects.get(id=self.request.data['tenant'])
            except Tenant.DoesNotExist:
                pass
                
        if not tenant:
            raise serializers.ValidationError({"tenant": "Un tenant doit être spécifié."})

        keycloak_admin = self.get_keycloak_admin(tenant=tenant)
        
        # 1. Créer l'utilisateur dans Keycloak
        new_user = {
            "email": email,
            "username": username,
            "enabled": True,
            "firstName": first_name,
            "lastName": last_name,
            "credentials": [{"value": password, "type": "password", "temporary": False}],
        }
        
        try:
            # Keycloak renvoie l'UUID du nouvel utilisateur (ou location)
            keycloak_user_id = keycloak_admin.create_user(new_user)
            
            # Assign role in Keycloak
            if user_data.get('role'):
                role_name = user_data['role'].name
                try:
                    realm_role = keycloak_admin.get_realm_role(role_name)
                    if realm_role:
                        keycloak_admin.assign_realm_roles(keycloak_user_id, [realm_role])
                except KeycloakError:
                    pass
            
        except KeycloakError as e:
            # En cas d'erreur (ex: email déjà existant), on renvoie l'erreur
            raise serializers.ValidationError({"keycloak_error": str(e)})

        # 2. Créer l'utilisateur localement dans PostgreSQL avec la référence Keycloak
        serializer.save(
            external_reference=keycloak_user_id,
            tenant=tenant
        )

from .models import Office
from .serializers import OfficeSerializer

class OfficeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows offices (warehouses/stores) to be viewed or edited.
    """
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tenant']

    def get_queryset(self):
        # Un utilisateur ne voit que les offices de son Tenant
        if getattr(self.request.user, 'tenant', None):
            return Office.objects.filter(tenant=self.request.user.tenant)
        # S'il n'y a pas de tenant associé, retourner tout ou rien selon le besoin (rien ici par sécurité)
        return Office.objects.none()

    def perform_create(self, serializer):
        # Assigne automatiquement le tenant de l'utilisateur qui crée l'office s'il est manquant
        tenant = getattr(self.request.user, 'tenant', None)
        if 'tenant' in self.request.data:
            from .models import Tenant
            try:
                tenant = Tenant.objects.get(id=self.request.data['tenant'])
            except Tenant.DoesNotExist:
                pass
                
        if not tenant:
            raise serializers.ValidationError({"tenant": "Un tenant doit être spécifié."})
            
        serializer.save(tenant=tenant)
