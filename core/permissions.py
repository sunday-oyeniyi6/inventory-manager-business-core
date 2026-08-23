from rest_framework.permissions import BasePermission
from django.core.cache import cache

class HasPermission(BasePermission):
    """
    Vérifie si l'utilisateur possède une permission spécifique via son rôle.
    Utilisation: permission_classes = [HasPermission.require('catalog:read')]
    """
    
    def __init__(self, required_permission=None):
        self.required_permission = required_permission

    def __call__(self):
        return self

    @classmethod
    def require(cls, required_permission):
        return cls(required_permission=required_permission)

    def has_permission(self, request, view):
        # Si aucune permission n'est requise, on laisse passer
        if not self.required_permission:
            return True
            
        # L'utilisateur doit être authentifié
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Les superusers ont tous les droits
        if request.user.is_superuser:
            return True

        # Vérifier si l'utilisateur a un rôle
        if not request.user.role:
            return False

        # Vérifier les permissions en cache pour éviter une requête SQL
        cache_key = f"role_permissions_{request.user.role.id}"
        permissions = cache.get(cache_key)

        if permissions is None:
            # Récupérer les permissions de la base de données
            permissions = list(request.user.role.permissions.values_list('code', flat=True))
            # Mettre en cache pour 1 heure (3600 secondes)
            cache.set(cache_key, permissions, 3600)

        return self.required_permission in permissions
