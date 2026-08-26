from django.db import models
from core.models import TenantScopedModel
from catalog.models import Product

class StockItem(TenantScopedModel):
    office = models.ForeignKey('core.Office', on_delete=models.CASCADE, related_name='stock_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('tenant', 'office', 'product')

    def __str__(self):
        return f"{self.product.name} in {self.office.name}: {self.quantity}"


class StockMovement(TenantScopedModel):
    class MovementType(models.TextChoices):
        IN = 'IN', 'Entrée'
        OUT = 'OUT', 'Sortie'
        ADJUSTMENT = 'ADJUSTMENT', 'Ajustement'

    office = models.ForeignKey('core.Office', on_delete=models.PROTECT, related_name='movements')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(
        max_length=20, 
        choices=MovementType.choices
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Quantité mouvementée")
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Référence document (ex: BL-123)")
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update StockItem quantity
            stock_item, created = StockItem.objects.get_or_create(
                tenant=self.tenant,
                office=self.office,
                product=self.product,
                defaults={'quantity': 0}
            )
            
            if self.movement_type == self.MovementType.IN:
                stock_item.quantity += self.quantity
            elif self.movement_type == self.MovementType.OUT:
                stock_item.quantity -= self.quantity
            elif self.movement_type == self.MovementType.ADJUSTMENT:
                # La quantité peut être négative ou positive pour un ajustement
                stock_item.quantity += self.quantity
                
            stock_item.save()

    def __str__(self):
        return f"{self.movement_type} - {self.quantity} of {self.product.name}"


class StockAlert(TenantScopedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    office = models.ForeignKey('core.Office', on_delete=models.CASCADE, related_name='alerts')
    minimum_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('tenant', 'product', 'office')

    def __str__(self):
        return f"Alert for {self.product.name} in {self.office.name}: Min {self.minimum_quantity}"
