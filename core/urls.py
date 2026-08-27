from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, RoleViewSet, TenantViewSet, OfficeViewSet, PublicTenantListView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'offices', OfficeViewSet, basename='office')

urlpatterns = [
    path('tenants/public/', PublicTenantListView.as_view(), name='tenant-public-list'),
    path('', include(router.urls)),
]
