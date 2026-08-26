from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from core.models import Tenant, Office
from catalog.models import Product, Category
from .models import StockItem, StockMovement, StockAlert

from decimal import Decimal

class InventoryModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.category = Category.objects.create(name="Electronics", tenant=self.tenant)
        self.product = Product.objects.create(
            name="Laptop", 
            sku="LPT-01", 
            category=self.category, 
            base_price=Decimal('1000.00'),
            tenant=self.tenant
        )
        self.office = Office.objects.create(
            name="Main Office", 
            location="Zone 1", 
            tenant=self.tenant
        )

    def test_create_office(self):
        self.assertEqual(self.office.name, "Main Office")
        self.assertEqual(str(self.office), "Main Office (Test Tenant)")

    def test_stock_movement_in_updates_stock_item(self):
        # Initial IN movement
        StockMovement.objects.create(
            tenant=self.tenant,
            office=self.office,
            product=self.product,
            movement_type=StockMovement.MovementType.IN,
            quantity=Decimal('50.00'),
            reference="IN-001"
        )
        
        # Check that StockItem was created and quantity is correct
        stock_item = StockItem.objects.get(tenant=self.tenant, office=self.office, product=self.product)
        self.assertEqual(stock_item.quantity, Decimal('50.00'))

    def test_stock_movement_out_updates_stock_item(self):
        # Add stock first
        StockMovement.objects.create(
            tenant=self.tenant,
            office=self.office,
            product=self.product,
            movement_type=StockMovement.MovementType.IN,
            quantity=Decimal('50.00'),
            reference="IN-002"
        )
        
        # Out movement
        StockMovement.objects.create(
            tenant=self.tenant,
            office=self.office,
            product=self.product,
            movement_type=StockMovement.MovementType.OUT,
            quantity=Decimal('20.00'),
            reference="OUT-001"
        )
        
        # Check remaining stock
        stock_item = StockItem.objects.get(tenant=self.tenant, office=self.office, product=self.product)
        self.assertEqual(stock_item.quantity, Decimal('30.00'))

class InventoryAPITests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant API")
        self.category = Category.objects.create(name="Phones", tenant=self.tenant)
        self.product = Product.objects.create(
            name="iPhone", 
            sku="IPHONE-12", 
            base_price=999.00, 
            category=self.category,
            tenant=self.tenant
        )
        self.office = Office.objects.create(
            name="API Office", 
            location="API-LOC", 
            tenant=self.tenant
        )

    def test_create_movement_api(self):
        url = reverse('stockmovement-list')
        data = {
            'office': self.office.id,
            'product': self.product.id,
            'movement_type': 'IN',
            'quantity': '100.00',
            'tenant': self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StockMovement.objects.count(), 1)
        
        # Verify stock item via API
        stock_item_url = reverse('stockitem-list')
        stock_response = self.client.get(stock_item_url)
        self.assertEqual(stock_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(stock_response.data), 1)
        self.assertEqual(float(stock_response.data[0]['quantity']), 100.00)

    def test_out_movement_insufficient_stock_should_fail(self):
        url = reverse('stockmovement-list')
        data = {
            'office': self.office.id,
            'product': self.product.id,
            'movement_type': 'OUT',
            'quantity': '50.00',
            'tenant': self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)

    def test_out_movement_success_api(self):
        # First IN movement
        url = reverse('stockmovement-list')
        self.client.post(url, {
            'office': self.office.id,
            'product': self.product.id,
            'movement_type': 'IN',
            'quantity': '10.00',
            'tenant': self.tenant.id
        }, format='json')
        
        # Then OUT movement
        response = self.client.post(url, {
            'office': self.office.id,
            'product': self.product.id,
            'movement_type': 'OUT',
            'quantity': '3.00',
            'tenant': self.tenant.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        stock_item = StockItem.objects.get(office=self.office, product=self.product)
        self.assertEqual(stock_item.quantity, 7.00)

    def test_create_stock_alert_api(self):
        url = reverse('stockalert-list')
        data = {
            "minimum_quantity": "5.00",
            "product": self.product.id,
            "office": self.office.id,
            "tenant": self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StockAlert.objects.count(), 1)

    # --- StockItem CRUD (ReadOnly) ---
    def test_list_stock_items_api(self):
        StockItem.objects.create(office=self.office, product=self.product, quantity=50.00, tenant=self.tenant)
        url = reverse('stockitem-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_stock_item_api(self):
        item = StockItem.objects.create(office=self.office, product=self.product, quantity=50.00, tenant=self.tenant)
        url = reverse('stockitem-detail', args=[item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['quantity']), 50.00)

    # --- StockMovement CRUD ---
    def test_list_stock_movements_api(self):
        StockMovement.objects.create(office=self.office, product=self.product, movement_type='IN', quantity=10, tenant=self.tenant)
        url = reverse('stockmovement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_stock_movement_api(self):
        mov = StockMovement.objects.create(office=self.office, product=self.product, movement_type='IN', quantity=10, tenant=self.tenant)
        url = reverse('stockmovement-detail', args=[mov.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_stock_movement_api(self):
        mov = StockMovement.objects.create(office=self.office, product=self.product, movement_type='IN', quantity=10, tenant=self.tenant)
        url = reverse('stockmovement-detail', args=[mov.id])
        data = {'notes': 'Updated note'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mov.refresh_from_db()
        self.assertEqual(mov.notes, 'Updated note')

    def test_delete_stock_movement_api(self):
        mov = StockMovement.objects.create(office=self.office, product=self.product, movement_type='IN', quantity=10, tenant=self.tenant)
        url = reverse('stockmovement-detail', args=[mov.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- StockAlert CRUD ---
    def test_list_stock_alerts_api(self):
        StockAlert.objects.create(office=self.office, product=self.product, minimum_quantity=5, tenant=self.tenant)
        url = reverse('stockalert-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_stock_alert_api(self):
        alert = StockAlert.objects.create(office=self.office, product=self.product, minimum_quantity=5, tenant=self.tenant)
        url = reverse('stockalert-detail', args=[alert.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_stock_alert_api(self):
        alert = StockAlert.objects.create(office=self.office, product=self.product, minimum_quantity=5, tenant=self.tenant)
        url = reverse('stockalert-detail', args=[alert.id])
        data = {'minimum_quantity': '10.00'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertEqual(alert.minimum_quantity, 10.00)

    def test_delete_stock_alert_api(self):
        alert = StockAlert.objects.create(office=self.office, product=self.product, minimum_quantity=5, tenant=self.tenant)
        url = reverse('stockalert-detail', args=[alert.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
