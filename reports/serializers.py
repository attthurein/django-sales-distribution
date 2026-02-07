from rest_framework import serializers
from .models import DailySalesSummary, DailyInventorySnapshot, DailyPaymentSummary, DailyExpenseSummary
from core.api_views import ProductSerializer

class DailySalesSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySalesSummary
        fields = [
            'id', 'date', 'total_revenue', 'total_orders',
            'total_items_sold', 'gross_profit', 'updated_at'
        ]

class DailyInventorySnapshotSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = DailyInventorySnapshot
        fields = [
            'id', 'date', 'product', 'product_detail',
            'quantity_on_hand', 'total_value', 'updated_at'
        ]

class DailyPaymentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPaymentSummary
        fields = [
            'id', 'date', 'total_collected', 'transaction_count', 'updated_at'
        ]

class DailyExpenseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyExpenseSummary
        fields = [
            'id', 'date', 'total_expense', 'transaction_count', 'updated_at'
        ]

class DashboardSummarySerializer(serializers.Serializer):
    revenue = serializers.FloatField()
    orders = serializers.IntegerField()
    payments = serializers.FloatField()
    expenses = serializers.FloatField()

class DashboardChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    revenue = serializers.ListField(child=serializers.FloatField())
    orders = serializers.ListField(child=serializers.IntegerField())
    payments = serializers.ListField(child=serializers.FloatField())
    expenses = serializers.ListField(child=serializers.FloatField())

class DashboardResponseSerializer(serializers.Serializer):
    today_summary = DashboardSummarySerializer()
    chart_data = DashboardChartDataSerializer()
