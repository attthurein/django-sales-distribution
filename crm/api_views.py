from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Lead, ContactLog, SampleDelivery
from .serializers import LeadSerializer, ContactLogSerializer, SampleDeliverySerializer

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'township', 'assigned_to']
    search_fields = ['name', 'phone', 'shop_name', 'contact_person']
    ordering_fields = ['created_at', 'name']

class ContactLogViewSet(viewsets.ModelViewSet):
    queryset = ContactLog.objects.all()
    serializer_class = ContactLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lead', 'customer', 'contact_type', 'created_by']
    ordering_fields = ['created_at', 'next_follow_up']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class SampleDeliveryViewSet(viewsets.ModelViewSet):
    queryset = SampleDelivery.objects.all()
    serializer_class = SampleDeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'lead', 'customer', 'product']
    ordering_fields = ['given_at', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
