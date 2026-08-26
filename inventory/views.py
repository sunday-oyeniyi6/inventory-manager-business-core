from rest_framework import viewsets
from .models import StockItem, StockMovement, StockAlert
from .serializers import (
    StockItemSerializer, 
    StockMovementSerializer, 
    StockAlertSerializer
)

class StockItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows stock items to be viewed.
    Stock items are automatically updated via Stock Movements and should not be created/edited directly.
    """
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    
    # Optional: add filters for office and product
    filterset_fields = ['office', 'product']

class StockMovementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stock movements to be viewed or created.
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    
    filterset_fields = ['office', 'product', 'movement_type']
    
    # Generally movements shouldn't be updated or deleted easily, 
    # but we'll leave it as ModelViewSet for now and restrict via permissions later if needed.

class StockAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stock alerts to be viewed or edited.
    """
    queryset = StockAlert.objects.all()
    serializer_class = StockAlertSerializer
    
    filterset_fields = ['office', 'product']
