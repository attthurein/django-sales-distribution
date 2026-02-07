from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from datetime import timedelta
from .models import DailySalesSummary, DailyInventorySnapshot, DailyPaymentSummary, DailyExpenseSummary
from .serializers import (
    DailySalesSummarySerializer, DailyInventorySnapshotSerializer,
    DailyPaymentSummarySerializer, DailyExpenseSummarySerializer,
    DashboardResponseSerializer
)

class DashboardViewSet(viewsets.ViewSet):
    """
    API endpoint for executive dashboard metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=DashboardResponseSerializer)
    def list(self, request):
        """
        Get dashboard summary and chart data.
        """
        # Get last 7 days including today
        today = timezone.now().date()
        dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        # Prepare data structure
        chart_data = {
            'labels': [d.strftime('%Y-%m-%d') for d in dates],
            'revenue': [],
            'orders': [],
            'payments': [],
            'expenses': []
        }
        
        # Fetch summaries
        sales_map = {
            s.date: s for s in DailySalesSummary.objects.filter(date__in=dates)
        }
        payment_map = {
            p.date: p for p in DailyPaymentSummary.objects.filter(date__in=dates)
        }
        expense_map = {
            e.date: e for e in DailyExpenseSummary.objects.filter(date__in=dates)
        }
        
        for d in dates:
            s = sales_map.get(d)
            p = payment_map.get(d)
            e = expense_map.get(d)
            
            chart_data['revenue'].append(float(s.total_revenue) if s else 0)
            chart_data['orders'].append(s.total_orders if s else 0)
            chart_data['payments'].append(float(p.total_collected) if p else 0)
            chart_data['expenses'].append(float(e.total_expense) if e else 0)

        # Today's Snapshot
        s_today = sales_map.get(today)
        p_today = payment_map.get(today)
        e_today = expense_map.get(today)
        
        today_summary = {
            'revenue': float(s_today.total_revenue) if s_today else 0,
            'orders': s_today.total_orders if s_today else 0,
            'payments': float(p_today.total_collected) if p_today else 0,
            'expenses': float(e_today.total_expense) if e_today else 0,
        }

        return Response({
            'today_summary': today_summary,
            'chart_data': chart_data
        })

class DailySalesSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailySalesSummary.objects.all()
    serializer_class = DailySalesSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'total_revenue']

class DailyInventorySnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyInventorySnapshot.objects.all()
    serializer_class = DailyInventorySnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'product']
    ordering_fields = ['date', 'total_value']

class DailyPaymentSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyPaymentSummary.objects.all()
    serializer_class = DailyPaymentSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'total_collected']

class DailyExpenseSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyExpenseSummary.objects.all()
    serializer_class = DailyExpenseSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'total_expense']
