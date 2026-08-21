from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BrandViewSet, ProductViewSet

# Création du routeur automatique de DRF
router = DefaultRouter()

# On "enregistre" nos ViewSets dans le routeur. 
# DRF va générer automatiquement toutes les URLs nécessaires (GET, POST, PUT, DELETE)
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'products', ProductViewSet, basename='product')

# Les URLs générées par le routeur sont incluses dans les patterns de l'application
urlpatterns = [
    path('', include(router.urls)),
]
