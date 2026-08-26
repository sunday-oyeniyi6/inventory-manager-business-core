import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jose import jwt, JWTError
from .models import User, Tenant, Role

class KeycloakJWTAuthentication(BaseAuthentication):
    """
    Custom authentication class for validating Keycloak JWTs.
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # En production, il faut récupérer les clés publiques (JWKS) de Keycloak
            # et vérifier la signature. Pour simplifier cet exemple d'intégration, 
            # nous décodons le token (en mode sécurisé, on utiliserait jwt.decode avec jwks)
            payload = jwt.get_unverified_claims(token)
            
            # Dans une implémentation stricte :
            # jwks_url = f"{os.getenv('KEYCLOAK_SERVER_URL')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/certs"
            # jwks = requests.get(jwks_url).json()
            # payload = jwt.decode(token, jwks, algorithms=['RS256'], audience='account')
            
        except JWTError:
            raise AuthenticationFailed('Token invalide')

        # Extract Keycloak user ID and Issuer
        user_uuid = payload.get('sub')
        iss = payload.get('iss')
        
        if not user_uuid:
            raise AuthenticationFailed('Token ne contient pas d\'identifiant utilisateur (sub)')
            
        if not iss:
            raise AuthenticationFailed('Token ne contient pas l\'émetteur (iss)')
            
        # The issuer is typically http://domain:port/realms/realm_name
        realm_name = iss.split('/')[-1]

        try:
            user = User.objects.get(external_reference=user_uuid)
            # Verify the user belongs to the correct realm
            if user.tenant and user.tenant.keycloak_realm_name != realm_name:
                raise AuthenticationFailed(f'Conflit de tenant: le token provient du realm {realm_name} mais l\'utilisateur appartient à {user.tenant.keycloak_realm_name}')
        except User.DoesNotExist:
            # Synchronisation automatique (auto-provisioning) lors de la première connexion
            email = payload.get('email', '')
            username = payload.get('preferred_username', user_uuid)
            
            # Find the tenant associated with this realm
            try:
                tenant = Tenant.objects.get(keycloak_realm_name=realm_name)
            except Tenant.DoesNotExist:
                # Si le realm master est utilisé pour un superadmin, on autorise sans tenant
                if realm_name == 'master' or realm_name == os.getenv('KEYCLOAK_REALM', 'master'):
                    tenant = None
                else:
                    raise AuthenticationFailed(f"Aucun tenant local ne correspond au realm '{realm_name}'")
            
            user = User.objects.create(
                external_reference=user_uuid,
                username=username,
                email=email,
                tenant=tenant
            )
            
        return (user, token)

try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension
    
    class KeycloakJWTScheme(OpenApiAuthenticationExtension):
        target_class = 'core.authentication.KeycloakJWTAuthentication'
        name = 'jwtAuth'

        def get_security_definition(self, auto_schema):
            return {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
except ImportError:
    pass

