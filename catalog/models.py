from django.db import models
from core.models import TenantScopedModel
from django.utils.text import slugify

class Category(TenantScopedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('tenant', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Brand(TenantScopedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    website = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('tenant', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TenantScopedModel):
    class ProductType(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard'
        SERIALIZED = 'SERIALIZED', 'Sérialisé'
        LICENSE = 'LICENSE', 'Licence'
        SERVICE = 'SERVICE', 'Service'
        
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    description = models.TextField(blank=True, null=True)
    product_type = models.CharField(
        max_length=20, 
        choices=ProductType.choices, 
        default=ProductType.STANDARD
    )
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Prix de vente de référence")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Prix d'achat de référence")
    
    is_taxable = models.BooleanField(default=True, help_text="Soumis à la taxe par défaut du client")
    is_active = models.BooleanField(default=True)
    
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'sku')

    def __str__(self):
        return f"[{self.sku}] {self.name}"
