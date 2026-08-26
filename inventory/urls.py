from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockItemViewSet, StockMovementViewSet, StockAlertViewSet

router = DefaultRouter()
router.register(r'stock-items', StockItemViewSet, basename='stockitem')
router.register(r'movements', StockMovementViewSet, basename='stockmovement')
router.register(r'alerts', StockAlertViewSet, basename='stockalert')

urlpatterns = [
    path('', include(router.urls)),
]
