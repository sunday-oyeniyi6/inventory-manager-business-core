from rest_framework import serializers
from .models import Category, Brand, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        # On inclut tous les champs du modèle dans l'API
        fields = '__all__'
        # Le slug est généré automatiquement, le tenant est géré en arrière-plan
        read_only_fields = ('slug', 'created_at', 'updated_at')

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('slug', 'created_at', 'updated_at')

class ProductSerializer(serializers.ModelSerializer):
    # Ajout de champs en lecture seule pour afficher le nom complet plutôt que juste l'ID
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
