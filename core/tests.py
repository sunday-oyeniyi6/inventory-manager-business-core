from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
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
        # Setup tenant realm name to match token
        self.tenant.keycloak_realm_name = "visiontech"
        self.tenant.save()
        
        # Simuler un token valide pour le manager
        mock_jwt.return_value = {
            "sub": "uuid-manager",
            "email": "manager@visiontech.com",
            "iss": "http://localhost:8080/auth/realms/visiontech"
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

    @patch('core.views.KeycloakAdmin')
    def test_tenant_creation_api(self, MockKeycloakAdmin):
        # On mock l'instance de KeycloakAdmin pour ne pas réellement appeler Keycloak
        # The view instantiates KeycloakAdmin twice, we can just patch the class.
        url = reverse('tenant-list')
        data = {
            "name": "Vision Tech",
            "default_tax_rate": "18.00"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tenant.objects.count(), 2) # Including the one in setUp
        
    def test_office_creation_api(self):
        url = reverse('office-list')
        data = {
            "name": "Entrepôt Central VISION TECH",
            "location": "Zone Industrielle Tech, Bâtiment 4",
            "tenant": self.tenant.id
        }
        # Office creation requires authentication
        self.client.force_authenticate(user=self.user_manager)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Role CRUD ---
    def test_list_roles_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('role-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('core.views.KeycloakAdmin')
    def test_create_role_api(self, MockKeycloakAdmin):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('role-list')
        response = self.client.post(url, {'name': 'TEST_ROLE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.filter(name='TEST_ROLE').count(), 1)

    @patch('core.views.KeycloakAdmin')
    def test_update_role_api(self, MockKeycloakAdmin):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('role-detail', args=[self.role_manager.id])
        response = self.client.patch(url, {'description': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.role_manager.refresh_from_db()
        self.assertEqual(self.role_manager.description, 'Updated')

    def test_delete_role_api(self):
        self.client.force_authenticate(user=self.user_manager)
        role = Role.objects.create(name="TO_DELETE")
        url = reverse('role-detail', args=[role.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Tenant CRUD ---
    def test_list_tenants_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('tenant-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_tenant_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('tenant-detail', args=[self.tenant.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_tenant_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('tenant-detail', args=[self.tenant.id])
        response = self.client.patch(url, {'default_tax_rate': '20.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.default_tax_rate, 20.00)

    def test_delete_tenant_api(self):
        self.client.force_authenticate(user=self.user_manager)
        t = Tenant.objects.create(name="Temp")
        url = reverse('tenant-detail', args=[t.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Employee CRUD ---
    def test_list_employees_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_employee_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('employee-detail', args=[self.user_employee.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'employee')

    def test_update_employee_api(self):
        self.client.force_authenticate(user=self.user_manager)
        url = reverse('employee-detail', args=[self.user_employee.id])
        response = self.client.patch(url, {'first_name': 'John'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_employee.refresh_from_db()
        self.assertEqual(self.user_employee.first_name, 'John')

    def test_delete_employee_api(self):
        self.client.force_authenticate(user=self.user_manager)
        emp = User.objects.create(username="temp_emp", tenant=self.tenant)
        url = reverse('employee-detail', args=[emp.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Office CRUD ---
    def test_list_offices_api(self):
        self.client.force_authenticate(user=self.user_manager)
        from .models import Office
        Office.objects.create(name="Office1", tenant=self.tenant)
        url = reverse('office-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_office_api(self):
        self.client.force_authenticate(user=self.user_manager)
        from .models import Office
        office = Office.objects.create(name="Office1", tenant=self.tenant)
        url = reverse('office-detail', args=[office.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Office1")

    def test_update_office_api(self):
        self.client.force_authenticate(user=self.user_manager)
        from .models import Office
        office = Office.objects.create(name="Office1", tenant=self.tenant)
        url = reverse('office-detail', args=[office.id])
        response = self.client.patch(url, {'location': 'Paris'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        office.refresh_from_db()
        self.assertEqual(office.location, 'Paris')

    def test_delete_office_api(self):
        self.client.force_authenticate(user=self.user_manager)
        from .models import Office
        office = Office.objects.create(name="Office1", tenant=self.tenant)
        url = reverse('office-detail', args=[office.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
