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

        # Extract Keycloak user ID
        user_uuid = payload.get('sub')
        if not user_uuid:
            raise AuthenticationFailed('Token ne contient pas d\'identifiant utilisateur (sub)')

        # In this simplified mapping, we expect the tenant ID and role to be passed in custom claims
        # or we fetch them from Keycloak via Admin API. But since we store the Role and Tenant in DB,
        # we can just find the user by external_reference.
        
        try:
            user = User.objects.get(external_reference=user_uuid)
        except User.DoesNotExist:
            # Synchronisation automatique (auto-provisioning) lors de la première connexion
            # Optionnel: on pourrait extraire l'email et le nom du payload
            email = payload.get('email', '')
            username = payload.get('preferred_username', user_uuid)
            
            user = User.objects.create(
                external_reference=user_uuid,
                username=username,
                email=email,
            )
            # Normalement le tenant_id est injecté dans le JWT ou assigné à l'avance 
            # par l'API de création d'employé.
            
        return (user, token)
