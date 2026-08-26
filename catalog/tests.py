from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from core.models import Tenant
from .models import Category, Brand, Product

class CatalogModelTests(TestCase):
    def setUp(self):
        # On crée un locataire de test (obligatoire car nos modèles en dépendent)
        self.tenant = Tenant.objects.create(name="Test Tenant")

    def test_create_category(self):
        category = Category.objects.create(name="Électronique", tenant=self.tenant)
        self.assertEqual(category.slug, "electronique")
        self.assertEqual(str(category), "Électronique")

    def test_create_brand(self):
        brand = Brand.objects.create(name="Apple", tenant=self.tenant)
        self.assertEqual(brand.slug, "apple")

    def test_create_product(self):
        category = Category.objects.create(name="Ordinateurs", tenant=self.tenant)
        brand = Brand.objects.create(name="Apple", tenant=self.tenant)
        product = Product.objects.create(
            name="MacBook Pro",
            sku="MBP-14",
            category=category,
            brand=brand,
            base_price=2000.00,
            tenant=self.tenant
        )
        self.assertEqual(product.sku, "MBP-14")
        self.assertEqual(str(product), "[MBP-14] MacBook Pro")
        self.assertEqual(product.category.name, "Ordinateurs")

class CatalogAPITests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant API")
        self.category = Category.objects.create(name="Smartphones", tenant=self.tenant)
        
    def test_get_categories(self):
        # 'category-list' est le nom généré automatiquement par le DefaultRouter
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # On vérifie qu'on a bien reçu 1 catégorie (celle créée dans le setUp)
        self.assertEqual(len(response.data), 1)

    def test_create_product_api_valid(self):
        url = reverse('product-list')
        data = {
            'name': 'iPhone 15',
            'sku': 'IP15-128',
            'base_price': '999.99',
            'category': self.category.id,
            'tenant': self.tenant.id # Nécessaire ici car on n'a pas encore de middleware de session
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.get().name, 'iPhone 15')
        
    def test_create_product_invalid_category_should_fail(self):
        url = reverse('product-list')
        data = {
            'name': 'iPhone 15',
            'sku': 'IP15-128',
            'base_price': '999.99',
            'category': 9999, # ID qui n'existe pas !
            'tenant': self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Et le message d'erreur doit concerner le champ 'category'
        self.assertIn('category', response.data)

    def test_create_brand_api(self):
        url = reverse('brand-list')
        data = {
            "name": "Dell",
            "website": "https://www.dell.com",
            "tenant": self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Brand.objects.count(), 1)

    def test_create_category_api(self):
        url = reverse('category-list')
        data = {
            "name": "Ordinateurs Portables",
            "description": "PC Portables pour professionnels et gamers",
            "tenant": self.tenant.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2) # Including the one from setUp

    def test_retrieve_category_api(self):
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Smartphones")

    def test_update_category_api(self):
        url = reverse('category-detail', args=[self.category.id])
        data = {'name': 'Téléphones intelligents'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Téléphones intelligents')

    def test_delete_category_api(self):
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_list_brands_api(self):
        Brand.objects.create(name="Samsung", tenant=self.tenant)
        url = reverse('brand-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_brand_api(self):
        brand = Brand.objects.create(name="Sony", tenant=self.tenant)
        url = reverse('brand-detail', args=[brand.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Sony")

    def test_update_brand_api(self):
        brand = Brand.objects.create(name="Nokia", tenant=self.tenant)
        url = reverse('brand-detail', args=[brand.id])
        data = {'name': 'Nokia Corp'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brand.refresh_from_db()
        self.assertEqual(brand.name, 'Nokia Corp')

    def test_delete_brand_api(self):
        brand = Brand.objects.create(name="HTC", tenant=self.tenant)
        url = reverse('brand-detail', args=[brand.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_products_api(self):
        brand = Brand.objects.create(name="LG", tenant=self.tenant)
        Product.objects.create(name="TV OLED", sku="TV-01", base_price=1500, category=self.category, brand=brand, tenant=self.tenant)
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_product_api(self):
        product = Product.objects.create(name="Radio", sku="RD-01", base_price=50, category=self.category, tenant=self.tenant)
        url = reverse('product-detail', args=[product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Radio")

    def test_update_product_api(self):
        product = Product.objects.create(name="Watch", sku="WT-01", base_price=200, category=self.category, tenant=self.tenant)
        url = reverse('product-detail', args=[product.id])
        data = {'base_price': '250.00'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.base_price, 250.00)

    def test_delete_product_api(self):
        product = Product.objects.create(name="Tablet", sku="TB-01", base_price=300, category=self.category, tenant=self.tenant)
        url = reverse('product-detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
