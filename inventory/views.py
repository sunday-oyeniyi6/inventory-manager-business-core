from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from .models import StockItem, StockMovement, StockAlert
from .serializers import (
    StockItemSerializer, 
    StockMovementSerializer, 
    StockAlertSerializer
)

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

class StockItemViewSet(TenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows stock items to be viewed.
    Stock items are automatically updated via Stock Movements and should not be created/edited directly.
    """
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    
    # Optional: add filters for office and product
    filterset_fields = ['office', 'product']

class StockMovementViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows stock movements to be viewed or created.
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    
    filterset_fields = ['office', 'product', 'movement_type']
    
    # Generally movements shouldn't be updated or deleted easily, 
    # but we'll leave it as ModelViewSet for now and restrict via permissions later if needed.

class StockAlertViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows stock alerts to be viewed or edited.
    """
    queryset = StockAlert.objects.all()
    serializer_class = StockAlertSerializer
    
    filterset_fields = ['office', 'product']
