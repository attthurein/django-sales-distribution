from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Product, ProductCategory, ProductVariant, ProductPriceTier, Batch, StockMovement
from core.serializers import (
    ProductSerializer, ProductCategorySerializer, ProductVariantSerializer,
    ProductPriceTierSerializer, BatchSerializer, StockMovementSerializer,
    StockAdjustmentSerializer
)

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.filter(deleted_at__isnull=True).order_by('name')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'sku']

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """
        Adjust stock for a product.
        Input: {
            "quantity": int (positive to add, negative to deduct),
            "reason": str,
            "expiry_date": date (optional, for batch adjustment)
        }
        """
        product = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            reason = serializer.validated_data['reason']
            expiry_date = serializer.validated_data.get('expiry_date')
            
            try:
                if expiry_date:
                    # Batch adjustment
                    batch = Batch.objects.filter(product=product, expiry_date=expiry_date).first()
                    if not batch:
                        if quantity < 0:
                            return Response(
                                {'error': f"Cannot deduct from non-existent batch (Expiry: {expiry_date})"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        # Create new batch
                        batch = Batch(
                            product=product,
                            batch_number=f"BATCH-{expiry_date.strftime('%Y%m%d')}",
                            quantity=0, # Will be added below
                            expiry_date=expiry_date,
                            notes=reason
                        )
                        batch.save()
                    
                    batch.quantity += quantity
                    batch.save()
                    msg = f"Batch adjusted by {quantity}. New batch stock: {batch.quantity}"
                else:
                    # Global adjustment
                    from core.services import adjust_stock
                    adjust_stock(
                        product_id=product.id,
                        quantity=quantity,
                        reason=reason,
                        approved_by=request.user,
                    )
                    product.refresh_from_db()
                    msg = f"Stock adjusted by {quantity}. New stock: {product.stock_quantity}"
                
                return Response({'status': 'success', 'message': msg})
                
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows product categories to be viewed or edited.
    """
    queryset = ProductCategory.objects.all().order_by('name_en')
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

class ProductPriceTierViewSet(viewsets.ModelViewSet):
    queryset = ProductPriceTier.objects.all()
    serializer_class = ProductPriceTierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'customer_type']

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product']
    ordering_fields = ['expiry_date', 'created_at']

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type', 'batch']
    ordering_fields = ['created_at']
