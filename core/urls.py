from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('', include(router.urls)),
]
