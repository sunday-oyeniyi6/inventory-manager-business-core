from rest_framework import serializers
from .models import Warehouse, StockItem, StockMovement, StockAlert

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'

class StockItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockItem
        fields = '__all__'
        read_only_fields = ('quantity',) # Quantities should only be updated via movements

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ('date',)

    def validate(self, data):
        """
        Check that OUT movements don't result in negative stock, 
        unless negative stock is explicitly allowed (not yet implemented).
        """
        if data.get('movement_type') == StockMovement.MovementType.OUT:
            warehouse = data.get('warehouse')
            product = data.get('product')
            quantity = data.get('quantity')
            tenant = data.get('tenant')

            # Look up current stock
            try:
                stock_item = StockItem.objects.get(
                    tenant=tenant, 
                    warehouse=warehouse, 
                    product=product
                )
                if stock_item.quantity < quantity:
                    raise serializers.ValidationError(
                        {"quantity": "Insufficient stock for this OUT movement."}
                    )
            except StockItem.DoesNotExist:
                raise serializers.ValidationError(
                    {"quantity": "No stock available for this product in this warehouse."}
                )

        return data

class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockAlert
        fields = '__all__'
