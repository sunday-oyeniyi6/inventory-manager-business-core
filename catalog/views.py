from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from .models import Category, Brand, Product
from .serializers import CategorySerializer, BrandSerializer, ProductSerializer

class TenantViewSetMixin:
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self.request.user, 'tenant', None):
            return self.queryset.filter(tenant=self.request.user.tenant)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant = getattr(self.request.user, 'tenant', None)
        if 'tenant' in self.request.data:
            from core.models import Tenant
            try:
                tenant = Tenant.objects.get(id=self.request.data['tenant'])
            except Tenant.DoesNotExist:
                pass
        
        if not tenant:
            raise serializers.ValidationError({"tenant": "Un tenant doit être spécifié."})
            
        serializer.save(tenant=tenant)

class CategoryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class BrandViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows brands to be viewed or edited.
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class ProductViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
