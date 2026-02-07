"""
Seed default master data.
"""
from django.core.management.base import BaseCommand

from master_data.models import (
    CustomerType, ReturnReason, ReturnType, PaymentMethod,
    OrderStatus, ReturnRequestStatus, ProductCategory, UnitOfMeasure, TaxRate,
    ContactType, Region, Township, Supplier, Currency,
)


class Command(BaseCommand):
    help = 'Seed default master data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up master data...')

        # CustomerType
        customer_types = [
            ('INDIVIDUAL', 'Individual', 'တစ်ဦးချင်း', 1),
            ('SHOP', 'Shop', 'ဆိုင်ငယ်', 2),
            ('DISTRIBUTOR', 'Distributor', 'ဖြန့်ချိရေး', 3),
        ]
        for code, name_en, name_my, sort_order in customer_types:
            CustomerType.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'sort_order': sort_order
            })
        self.stdout.write('  - CustomerType: OK')

        # ReturnReason
        return_reasons = [
            ('EXPIRED', 'Expired', 'သက်တမ်းကုန်', False),
            ('DAMAGED', 'Damaged', 'ပျက်စီး', True),
            ('WRONG_QTY', 'Wrong Quantity', 'အရေအတွက်မမှန်', True),
            ('QUALITY', 'Quality Issues', 'အရည်အသွေးပြဿနာ', True),
            ('OTHER', 'Other', 'အခြား', True),
        ]
        for code, name_en, name_my, requires_notes in return_reasons:
            ReturnReason.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'requires_notes': requires_notes
            })
        self.stdout.write('  - ReturnReason: OK')

        # ReturnType
        return_types = [
            ('REFUND', 'Refund', 'ငွေပြန်အမ်းခြင်း'),
            ('REPLACEMENT', 'Replacement', 'အစားထိုးပေးခြင်း'),
            ('EXCHANGE', 'Exchange', 'လဲလှယ်ခြင်း'),
            ('CREDIT_NOTE', 'Credit Note', 'အကြွေးမှတ်ချက်'),
        ]
        for code, name_en, name_my in return_types:
            ReturnType.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my
            })
        self.stdout.write('  - ReturnType: OK')

        # PaymentMethod
        payment_methods = [
            ('CASH', 'Cash', 'ငွေသား'),
            ('BANK', 'Bank Transfer', 'ဘဏ်လွှဲ'),
            ('CREDIT', 'Credit', 'အကြွေး'),
            ('MOBILE', 'Mobile Money', 'မိုဘိုင်းငွေ'),
            ('OTHER', 'Other', 'အခြား'),
        ]
        for code, name_en, name_my in payment_methods:
            PaymentMethod.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my
            })
        self.stdout.write('  - PaymentMethod: OK')

        # OrderStatus
        order_statuses = [
            ('PENDING', 'Pending', 'ဆိုင်းငံ့', 1),
            ('CONFIRMED', 'Confirmed', 'အတည်ပြု', 2),
            ('DELIVERED', 'Delivered', 'ပို့ဆောင်ပြီး', 3),
            ('PAID', 'Paid', 'ငွေရှင်း', 4),
            ('CANCELLED', 'Cancelled', 'ပယ်ဖျက်', 5),
        ]
        for code, name_en, name_my, sort_order in order_statuses:
            OrderStatus.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'sort_order': sort_order
            })
        self.stdout.write('  - OrderStatus: OK')

        # ReturnRequestStatus
        return_statuses = [
            ('PENDING', 'Pending', 'ဆိုင်းငံ့', 1),
            ('APPROVED', 'Approved', 'အတည်ပြု', 2),
            ('REJECTED', 'Rejected', 'ပယ်ချ', 3),
            ('COMPLETED', 'Completed', 'ပြီးမြောက်', 4),
        ]
        for code, name_en, name_my, sort_order in return_statuses:
            ReturnRequestStatus.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'sort_order': sort_order
            })
        self.stdout.write('  - ReturnRequestStatus: OK')

        # ProductCategory
        categories = [
            ('GENERAL', 'General', 'အထွေထွေ', 1),
            ('BEVERAGE', 'Beverage', 'အဖျော်ရည်', 2),
            ('SNACK', 'Snack', 'အစားအစာ', 3),
        ]
        for code, name_en, name_my, sort_order in categories:
            ProductCategory.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'sort_order': sort_order
            })
        self.stdout.write('  - ProductCategory: OK')

        # UnitOfMeasure
        units = [
            ('PCS', 'Piece', 'ပဲခွဲ'),
            ('BOX', 'Box', 'ဘူး'),
            ('CARTON', 'Carton', 'ကာတန်'),
            ('PKG', 'Package', 'ဘူးအစု'),
        ]
        for code, name_en, name_my in units:
            UnitOfMeasure.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my
            })
        self.stdout.write('  - UnitOfMeasure: OK')

        # TaxRate
        TaxRate.objects.get_or_create(code='COMMERCIAL', defaults={
            'name_en': 'Commercial Tax', 'name_my': 'ကူးသန်းရောင်းဝယ်ခွန်',
            'rate_percent': 5
        })
        self.stdout.write('  - TaxRate: OK')

        # Currency (base currency for whole system)
        currencies = [
            ('MMK', 'Myanmar Kyat', 'ကျပ်ငွေ', 'Ks', 1),
            ('USD', 'US Dollar', 'ဒေါ်လာ', '$', 2),
            ('THB', 'Thai Baht', 'ဘတ်', '฿', 3),
        ]
        for code, name_en, name_my, symbol, sort_order in currencies:
            Currency.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my,
                'symbol': symbol, 'sort_order': sort_order
            })
        self.stdout.write('  - Currency: OK')

        # ContactType (for CRM contact logs)
        contact_types = [
            ('PHONE', 'Phone', 'ဖုန်း', 1),
            ('VISIT', 'Visit', 'သွားရောက်တွေ့ဆုံ', 2),
            ('EMAIL', 'Email', 'အီးမေးလ်', 3),
            ('MEETING', 'Meeting', 'အစည်းအဝေး', 4),
            ('OTHER', 'Other', 'အခြား', 5),
        ]
        for code, name_en, name_my, sort_order in contact_types:
            ContactType.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my, 'sort_order': sort_order
            })
        self.stdout.write('  - ContactType: OK')

        # Region & Township (for customer address, CRM)
        regions_data = [
            ('YGN', 'Yangon', 'ရန်ကုန်'),
            ('MDY', 'Mandalay', 'မန္တလေး'),
            ('OTH', 'Other', 'အခြား'),
        ]
        for code, name_en, name_my in regions_data:
            region, _ = Region.objects.get_or_create(code=code, defaults={
                'name_en': name_en, 'name_my': name_my
            })
            if code == 'YGN':
                townships_data = [
                    ('BTH', 'Botahtaung', 'ဗိုလ်တထောင်', 0),
                    ('DGT', 'Dagon', 'ဒဂုံ', 0),
                    ('HLA', 'Hlaing', 'ဟိုင်းကြီး', 0),
                    ('KMY', 'Kamayut', 'ကမာရွတ်', 0),
                    ('LMD', 'Lammadaw', 'လမ်းမတော်', 0),
                ]
                for t_code, t_en, t_my, fee in townships_data:
                    Township.objects.get_or_create(
                        code=f'{code}_{t_code}',
                        defaults={
                            'name_en': t_en, 'name_my': t_my,
                            'region': region, 'delivery_fee': fee
                        }
                    )
        self.stdout.write('  - Region & Township: OK')

        # Supplier (sample for purchasing)
        Supplier.objects.get_or_create(code='DEFAULT', defaults={
            'name_en': 'Default Supplier', 'name_my': 'ပုံမှန်ပေးသွင်းသူ'
        })
        self.stdout.write('  - Supplier: OK')

        self.stdout.write(self.style.SUCCESS('Master data setup complete!'))
