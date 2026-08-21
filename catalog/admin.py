from django.contrib import admin
from .models import Category, Brand, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'parent', 'slug')
    list_filter = ('tenant',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'website')
    list_filter = ('tenant',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'tenant', 'product_type', 'category', 'brand', 'base_price', 'is_active')
    list_filter = ('tenant', 'product_type', 'is_active', 'category', 'brand')
    search_fields = ('name', 'sku', 'barcode')
    list_editable = ('is_active', 'base_price')
