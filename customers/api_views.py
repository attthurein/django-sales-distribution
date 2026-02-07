from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from customers.models import Customer, Salesperson
from customers.serializers import CustomerSerializer, SalespersonSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing customers.
    """
    queryset = Customer.objects.filter(deleted_at__isnull=True).order_by('name')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer_type', 'township', 'salesperson', 'is_active']
    search_fields = ['name', 'shop_name', 'contact_person', 'phone']
    ordering_fields = ['name', 'created_at']

class SalespersonViewSet(viewsets.ModelViewSet):
    queryset = Salesperson.objects.filter(deleted_at__isnull=True).order_by('name')
    serializer_class = SalespersonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone']
