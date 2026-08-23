from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from .models import Tenant, Role, Permission, User
from .permissions import HasPermission
from django.contrib.auth import get_user_model

class CoreSecurityTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Vision Tech")
        
        self.perm_read = Permission.objects.create(code="catalog:read", name="Read Catalog")
        self.perm_write = Permission.objects.create(code="catalog:write", name="Write Catalog")
        
        self.role_manager = Role.objects.create(name="MANAGER")
        self.role_manager.permissions.add(self.perm_read, self.perm_write)
        
        self.role_employee = Role.objects.create(name="EMPLOYEE")
        self.role_employee.permissions.add(self.perm_read)
        
        self.user_manager = User.objects.create(
            username="manager",
            external_reference="uuid-manager",
            tenant=self.tenant,
            role=self.role_manager
        )
        
        self.user_employee = User.objects.create(
            username="employee",
            external_reference="uuid-employee",
            tenant=self.tenant,
            role=self.role_employee
        )
        
        self.client = APIClient()

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.user_manager.role.name, "MANAGER")
        
    def test_has_permission_class(self):
        # Create a mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user

        req_manager = MockRequest(self.user_manager)
        req_employee = MockRequest(self.user_employee)
        
        perm_checker_write = HasPermission(required_permission="catalog:write")
        perm_checker_read = HasPermission(required_permission="catalog:read")
        
        # Manager has both read and write
        self.assertTrue(perm_checker_write.has_permission(req_manager, None))
        self.assertTrue(perm_checker_read.has_permission(req_manager, None))
        
        # Employee has only read
        self.assertFalse(perm_checker_write.has_permission(req_employee, None))
        self.assertTrue(perm_checker_read.has_permission(req_employee, None))

    @patch('core.authentication.jwt.get_unverified_claims')
    def test_jwt_authentication(self, mock_jwt):
        # Simuler un token valide pour le manager
        mock_jwt.return_value = {
            "sub": "uuid-manager",
            "email": "manager@visiontech.com"
        }
        
        # Ce test est plus complexe à faire sans endpoint spécifique.
        # On va appeler l'endpoint /api/v1/core/roles/ avec le token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer faketoken123')
        response = self.client.get('/api/v1/core/roles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # On vérifie que la réponse contient 2 rôles
        self.assertEqual(len(response.data), 2)
        
    @patch('core.views.KeycloakAdmin.create_user')
    def test_employee_creation_api(self, mock_kc_create):
        # Simuler la création dans keycloak
        mock_kc_create.return_value = "new-uuid-456"
        
        # Authentifier en tant que manager
        self.client.force_authenticate(user=self.user_manager)
        
        data = {
            "username": "new_emp",
            "email": "new@visiontech.com",
            "first_name": "New",
            "last_name": "Emp",
            "role_id": self.role_employee.id,
            "password": "Password123!"
        }
        
        response = self.client.post('/api/v1/core/employees/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier en DB
        new_user = User.objects.get(username="new_emp")
        self.assertEqual(new_user.external_reference, "new-uuid-456")
        self.assertEqual(new_user.tenant, self.tenant)
        self.assertEqual(new_user.role, self.role_employee)
