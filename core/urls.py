from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, RoleViewSet, TenantViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]
