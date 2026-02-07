from rest_framework import viewsets, permissions
from core.models import Product, ProductCategory
from core.serializers import ProductSerializer, ProductCategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.filter(deleted_at__isnull=True).order_by('name')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows product categories to be viewed or edited.
    """
    queryset = ProductCategory.objects.all().order_by('name_en')
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
