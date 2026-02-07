from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from orders.models import SalesOrder, Payment
from orders.serializers import SalesOrderSerializer, CreateOrderSerializer, PaymentSerializer

class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing sales orders.
    """
    queryset = SalesOrder.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return SalesOrderSerializer
        
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'order_type', 'order_date']
    search_fields = ['order_number', 'customer__name']
    ordering_fields = ['created_at', 'total_amount', 'order_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm the order."""
        order = self.get_object()
        from master_data.constants import ORDER_CONFIRMED
        from master_data.models import OrderStatus
        from django.db import transaction
        
        try:
            with transaction.atomic():
                order.status = OrderStatus.get_by_code(ORDER_CONFIRMED)
                order.save(update_fields=['status'])
            return Response({'status': 'order confirmed'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Mark order as delivered and deduct stock."""
        order = self.get_object()
        from orders.services import deliver_order
        try:
            deliver_order(order_id=order.pk, user=request.user)
            return Response({'status': 'order delivered'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel the order."""
        order = self.get_object()
        from orders.services import cancel_order
        try:
            cancel_order(order_id=order.pk, user=request.user)
            return Response({'status': 'order cancelled'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.filter(deleted_at__isnull=True).order_by('-payment_date')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['order', 'payment_method', 'payment_date']
    search_fields = ['voucher_number', 'reference_number', 'order__order_number']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
