from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, F
from reports.models import DailySalesSummary, DailyInventorySnapshot, DailyPaymentSummary, DailyExpenseSummary
from orders.models import SalesOrder, OrderItem, Payment
from accounting.models import Expense
from core.models import Product, StockMovement
import datetime

class Command(BaseCommand):
    help = 'Generate daily sales and inventory reports'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='YYYY-MM-DD')
        parser.add_argument('--all', action='store_true', help='Generate for all past dates')

    def handle(self, *args, **options):
        if options['all']:
            # Find first order date or movement date
            first_order = SalesOrder.objects.order_by('created_at').first()
            first_mvmt = StockMovement.objects.order_by('created_at').first()
            
            dates = []
            if first_order: dates.append(first_order.created_at.date())
            if first_mvmt: dates.append(first_mvmt.created_at.date())
            
            if not dates:
                start_date = timezone.now().date()
            else:
                start_date = min(dates)
                
            end_date = timezone.now().date() - datetime.timedelta(days=1)
            
            current = start_date
            while current <= end_date:
                self.generate_for_date(current)
                current += datetime.timedelta(days=1)
        else:
            date_str = options['date']
            if date_str:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                target_date = timezone.now().date() - datetime.timedelta(days=1)
            self.generate_for_date(target_date)

    def generate_for_date(self, date):
        self.stdout.write(f"Generating reports for {date}...")
        
        # 1. Sales Summary
        orders = SalesOrder.objects.filter(
            created_at__date=date,
            deleted_at__isnull=True
        )
        
        agg = orders.aggregate(
            total_rev=Sum('total_amount'),
            count=Count('id')
        )
        
        total_revenue = agg['total_rev'] or 0
        total_orders = agg['count'] or 0
        
        # Calculate items sold
        total_items = OrderItem.objects.filter(
            order__created_at__date=date,
            order__deleted_at__isnull=True
        ).aggregate(qty=Sum('quantity'))['qty'] or 0
        
        # Gross profit calculation
        # Note: Ideally cost should be captured at time of sale (in OrderItem)
        # Here we use current cost_price as an approximation
        gross_profit = 0
        for order in orders:
            # Optimize: prefetch items
            for item in order.orderitem_set.all():
                cost = item.product.cost_price or item.product.base_price or 0
                item_profit = (item.unit_price - cost) * item.quantity
                gross_profit += item_profit

        DailySalesSummary.objects.update_or_create(
            date=date,
            defaults={
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'total_items_sold': total_items,
                'gross_profit': gross_profit
            }
        )

        # 2. Payment Summary
        payments = Payment.objects.filter(
            payment_date=date,
            deleted_at__isnull=True
        )
        pay_agg = payments.aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        DailyPaymentSummary.objects.update_or_create(
            date=date,
            defaults={
                'total_collected': pay_agg['total'] or 0,
                'transaction_count': pay_agg['count'] or 0
            }
        )

        # 3. Expense Summary
        expenses = Expense.objects.filter(
            date=date,
            deleted_at__isnull=True
        )
        exp_agg = expenses.aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        DailyExpenseSummary.objects.update_or_create(
            date=date,
            defaults={
                'total_expense': exp_agg['total'] or 0,
                'transaction_count': exp_agg['count'] or 0
            }
        )

        # 4. Inventory Snapshot
        # Logic: Stock @ Date = Current Stock - Sum(Movements AFTER Date)
        
        # Get movements strictly after the target date (starting from next day 00:00)
        # Since created_at is DateTime, we compare against date + 1 day
        next_day_start = date + datetime.timedelta(days=1)
        
        # Pre-calculate movement deltas for all products
        # We need to sum quantities for all movements where created_at__date >= next_day_start
        # Actually created_at__gte=next_day_start is more precise
        
        future_movements = StockMovement.objects.filter(
            created_at__date__gte=next_day_start
        ).values('product').annotate(total_change=Sum('quantity'))
        
        future_change_map = {m['product']: m['total_change'] for m in future_movements}
        
        products = Product.objects.all()
        for p in products:
            current_stock = p.stock_quantity
            # If we had movements after this date, subtract them to go back in time
            # e.g. Current=10, Tomorrow we added 5. Stock today was 5. (10 - 5 = 5)
            # e.g. Current=10, Tomorrow we sold 2 (qty=-2). Stock today was 12. (10 - (-2) = 12)
            change_after = future_change_map.get(p.id, 0)
            stock_at_date = current_stock - change_after
            
            val_price = p.cost_price or p.base_price or 0
            
            DailyInventorySnapshot.objects.update_or_create(
                date=date,
                product=p,
                defaults={
                    'quantity_on_hand': stock_at_date,
                    'total_value': stock_at_date * val_price
                }
            )
            
        self.stdout.write(self.style.SUCCESS(f"Completed report generation for {date}"))
