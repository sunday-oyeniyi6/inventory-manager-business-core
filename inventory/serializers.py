from rest_framework import serializers
from .models import StockItem, StockMovement, StockAlert

class StockItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)

    class Meta:
        model = StockItem
        fields = '__all__'
        read_only_fields = ('quantity', 'tenant') # Quantities should only be updated via movements

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ('date', 'tenant')

    def validate(self, data):
        """
        Check that OUT movements don't result in negative stock, 
        unless negative stock is explicitly allowed (not yet implemented).
        """
        if data.get('movement_type') == StockMovement.MovementType.OUT:
            office = data.get('office')
            product = data.get('product')
            quantity = data.get('quantity')
            
            # Since tenant is read_only, it's not in data. Fetch it from office
            tenant = office.tenant if office else None

            # Look up current stock
            try:
                stock_item = StockItem.objects.get(
                    tenant=tenant, 
                    office=office, 
                    product=product
                )
                if stock_item.quantity < quantity:
                    raise serializers.ValidationError(
                        {"quantity": "Insufficient stock for this OUT movement."}
                    )
            except StockItem.DoesNotExist:
                raise serializers.ValidationError(
                    {"quantity": "No stock available for this product in this office."}
                )

        return data

class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)

    class Meta:
        model = StockAlert
        fields = '__all__'
        read_only_fields = ('tenant',)
