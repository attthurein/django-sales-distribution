from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from core.models import Product, StockMovement

class Command(BaseCommand):
    help = 'Reconcile Product.stock_quantity based on StockMovement history (Rule 1: Stock is derived from movements)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually update the product stock quantity to match movements',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting stock reconciliation...")
        
        products = Product.all_objects.all().iterator() # Include soft-deleted products just in case
        mismatch_count = 0
        
        for product in products:
            # Calculate expected stock from movements
            # IN, RETURN, ADJUST (positive quantity in DB?)
            # Wait, looking at core/models.py:
            # quantity = models.IntegerField() # Positive for IN/RETURN, negative for OUT
            # So we just Sum('quantity')
            
            aggregated = StockMovement.objects.filter(product=product).aggregate(total=Sum('quantity'))
            calculated_stock = aggregated['total'] or 0
            
            current_stock = product.stock_quantity
            
            if current_stock != calculated_stock:
                mismatch_count += 1
                msg = f"MISMATCH: {product.name} (ID: {product.id}) | Current: {current_stock} | Calculated: {calculated_stock}"
                self.stdout.write(self.style.WARNING(msg))
                
                if options['fix']:
                    with transaction.atomic():
                        product.stock_quantity = calculated_stock
                        product.save(update_fields=['stock_quantity'])
                    self.stdout.write(self.style.SUCCESS(f"  -> FIXED: Updated to {calculated_stock}"))
            else:
                if options['verbosity'] > 1:
                    self.stdout.write(f"OK: {product.name} ({current_stock})")

        if mismatch_count == 0:
            self.stdout.write(self.style.SUCCESS("All products are in sync!"))
        else:
            self.stdout.write(self.style.WARNING(f"Found {mismatch_count} products with stock mismatches."))
            if not options['fix']:
                self.stdout.write("Run with --fix to update product stock quantities.")
