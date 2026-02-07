from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ReturnRequest, ReturnItem, ReturnProcessing
from .serializers import ReturnRequestSerializer, ReturnRequestCreateSerializer, ReturnItemSerializer, ReturnProcessingSerializer

class ReturnRequestViewSet(viewsets.ModelViewSet):
    queryset = ReturnRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'return_type', 'order']
    search_fields = ['return_number', 'order__order_number']
    ordering_fields = ['created_at', 'return_number']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReturnRequestCreateSerializer
        return ReturnRequestSerializer

class ReturnItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReturnItem.objects.all()
    serializer_class = ReturnItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['return_request', 'product', 'reason']

class ReturnProcessingViewSet(viewsets.ModelViewSet):
    queryset = ReturnProcessing.objects.all()
    serializer_class = ReturnProcessingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['return_request', 'action']

    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)
