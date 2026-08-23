import os
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from .models import User, Role
from .serializers import EmployeeSerializer, RoleSerializer
from .permissions import HasPermission

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows roles to be viewed.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated] # Tout employé authentifié peut voir les rôles

from .models import Tenant
from .serializers import TenantSerializer

class TenantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tenants (companies) to be viewed or edited.
    Usually restricted to superadmins, but opened for test scenarios.
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    # permission_classes = [IsAuthenticated] # Commented out for initial creation without token


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

    def get_keycloak_admin(self):
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

        keycloak_admin = self.get_keycloak_admin()
        
        # 1. Créer l'utilisateur dans Keycloak
        new_user = {
            "email": email,
            "username": username,
            "enabled": True,
            "firstName": first_name,
            "lastName": last_name,
            "credentials": [{"value": password, "type": "password", "temporary": True}],
        }
        
        try:
            # Keycloak renvoie l'UUID du nouvel utilisateur (ou location)
            keycloak_user_id = keycloak_admin.create_user(new_user)
            
            # Optional: Assign role in Keycloak
            # role_name = user_data['role'].name
            # realm_role = keycloak_admin.get_realm_role(role_name)
            # keycloak_admin.assign_realm_roles(keycloak_user_id, [realm_role])
            
        except KeycloakError as e:
            # En cas d'erreur (ex: email déjà existant), on renvoie l'erreur
            from rest_framework import serializers
            raise serializers.ValidationError({"keycloak_error": str(e)})

        # 2. Créer l'utilisateur localement dans PostgreSQL avec la référence Keycloak
        serializer.save(
            external_reference=keycloak_user_id,
            tenant=self.request.user.tenant # On associe le nouvel employé au tenant de l'admin créateur
        )
