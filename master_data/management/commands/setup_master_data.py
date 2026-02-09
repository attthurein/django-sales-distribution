"""
Seed default master data.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from master_data.models import (
    CustomerType, ReturnReason, ReturnType, PaymentMethod,
    OrderStatus, ReturnRequestStatus, ProductCategory, UnitOfMeasure, TaxRate,
    ContactType, Region, Township, Supplier, Currency, Country
)


class Command(BaseCommand):
    help = 'Seed default master data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up master data...')

        # Country
        country, _ = Country.objects.get_or_create(code='MM', defaults={
            'name_en': 'Myanmar', 'name_my': 'မြန်မာ'
        })
        self.stdout.write('  - Country: OK')

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
        MYANMAR_LOCATIONS = [
            {
                "code": "YGN",
                "name_en": "Yangon Region",
                "name_my": "ရန်ကုန်တိုင်းဒေသကြီး",
                "townships": [
                    ("ALA", "Ahlone", "အလုံ"),
                    ("BTH", "Botahtaung", "ဗိုလ်တထောင်"),
                    ("Dagon", "Dagon", "ဒဂုံ"),
                    ("Dagon Seikkan", "Dagon Seikkan", "ဒဂုံဆိပ်ကမ်း"),
                    ("East Dagon", "East Dagon", "ဒဂုံအရှေ့ပိုင်း"),
                    ("North Dagon", "North Dagon", "ဒဂုံမြောက်ပိုင်း"),
                    ("South Dagon", "South Dagon", "ဒဂုံတောင်ပိုင်း"),
                    ("Dala", "Dala", "ဒလ"),
                    ("Dawbon", "Dawbon", "ဒေါပုံ"),
                    ("Hlaing", "Hlaing", "လှိုင်"),
                    ("Hlaingthaya", "Hlaingthaya", "လှိုင်သာယာ"),
                    ("Insein", "Insein", "အင်းစိန်"),
                    ("Kamayut", "Kamayut", "ကမာရွတ်"),
                    ("Kyauktada", "Kyauktada", "ကျောက်တံတား"),
                    ("Kyimyindaing", "Kyimyindaing", "ကြည့်မြင်တိုင်"),
                    ("Lanmadaw", "Lanmadaw", "လမ်းမတော်"),
                    ("Latha", "Latha", "လသာ"),
                    ("Mayangone", "Mayangone", "မရမ်းကုန်း"),
                    ("Mingala Taungnyunt", "Mingala Taungnyunt", "မင်္ဂလာတောင်ညွန့်"),
                    ("Mingaladon", "Mingaladon", "မင်္ဂလာဒုံ"),
                    ("North Okkalapa", "North Okkalapa", "မြောက်ဥက္ကလာပ"),
                    ("South Okkalapa", "South Okkalapa", "တောင်ဥက္ကလာပ"),
                    ("Pabedan", "Pabedan", "ပန်းဘဲတန်း"),
                    ("Pazundaung", "Pazundaung", "ပုဇွန်တောင်"),
                    ("Sanchaung", "Sanchaung", "စမ်းချောင်း"),
                    ("Seikkan", "Seikkan", "ဆိပ်ကမ်း"),
                    ("Shwepyitha", "Shwepyitha", "ရွှေပြည်သာ"),
                    ("Tamwe", "Tamwe", "တာမွေ"),
                    ("Thaketa", "Thaketa", "သာကေတ"),
                    ("Thingangyun", "Thingangyun", "သင်္ဃန်းကျွန်း"),
                    ("Yankin", "Yankin", "ရန်ကင်း"),
                    ("Hlegu", "Hlegu", "လှည်းကူး"),
                    ("Hmawbi", "Hmawbi", "မှော်ဘီ"),
                    ("Htantabin", "Htantabin", "ထန်းတပင်"),
                    ("Kawhmu", "Kawhmu", "ကော့မှူး"),
                    ("Kayan", "Kayan", "ခရမ်း"),
                    ("Kungyangon", "Kungyangon", "ကွမ်းခြံကုန်း"),
                    ("Kyauktan", "Kyauktan", "ကျောက်တန်း"),
                    ("Taikkyi", "Taikkyi", "တိုက်ကြီး"),
                    ("Thanlyin", "Thanlyin", "သန်လျင်"),
                    ("Thongwa", "Thongwa", "သုံးခွ"),
                    ("Twantay", "Twantay", "တွံတေး"),
                ]
            },
            {
                "code": "MDY",
                "name_en": "Mandalay Region",
                "name_my": "မန္တလေးတိုင်းဒေသကြီး",
                "townships": [
                    ("Amarkapura", "Amarapura", "အမရပူရ"),
                    ("Aungmyethazan", "Aungmyethazan", "အောင်မြေသာစံ"),
                    ("Chanayethazan", "Chanayethazan", "ချမ်းအေးသာစံ"),
                    ("Chanmyathazi", "Chanmyathazi", "ချမ်းမြသာစည်"),
                    ("Mahaaungmye", "Mahaaungmye", "မဟာအောင်မြေ"),
                    ("Patheingyi", "Patheingyi", "ပုသိမ်ကြီး"),
                    ("Pyigyidagun", "Pyigyidagun", "ပြည်ကြီးတံခွန်"),
                    ("Kyaukpadung", "Kyaukpadung", "ကျောက်ပန်းတောင်း"),
                    ("Kyaukse", "Kyaukse", "ကျောက်ဆည်"),
                    ("Madaya", "Madaya", "မတ္တရာ"),
                    ("Mahlaing", "Mahlaing", "မလှိုင်"),
                    ("Meiktila", "Meiktila", "မိတ္ထီလာ"),
                    ("Myingyan", "Myingyan", "မြင်းခြံ"),
                    ("Myittha", "Myittha", "မြစ်သား"),
                    ("Natogyi", "Natogyi", "နွားထိုးကြီး"),
                    ("Ngazun", "Ngazun", "ငါးဇွန်"),
                    ("Nyaung-U", "Nyaung-U", "ညောင်ဦး"),
                    ("Pyawbwe", "Pyawbwe", "ပျော်ဘွယ်"),
                    ("Pyinoolwin", "Pyinoolwin", "ပြင်ဦးလွင်"),
                    ("Singu", "Singu", "စဥ့်ကူး"),
                    ("Sintgaing", "Sintgaing", "စဥ့်ကိုင်"),
                    ("Tada-U", "Tada-U", "တံတားဦး"),
                    ("Taungtha", "Taungtha", "တောင်သာ"),
                    ("Thabeikkyin", "Thabeikkyin", "သပိတ်ကျင်း"),
                    ("Thazi", "Thazi", "သာစည်"),
                    ("Wundwin", "Wundwin", "ဝမ်းတွင်း"),
                    ("Yamethin", "Yamethin", "ရမည်းသင်း"),
                ]
            },
            {
                "code": "NPT",
                "name_en": "Naypyidaw Union Territory",
                "name_my": "နေပြည်တော် ပြည်ထောင်စုနယ်မြေ",
                "townships": [
                    ("DetKhiNaThiRi", "Dekkhinathiri", "ဒက္ခိဏသီရိ"),
                    ("Lewe", "Lewe", "လယ်ဝေး"),
                    ("OkeTaRaThiRi", "Ottarathiri", "ဥတ္တရသီရိ"),
                    ("Pobbathiri", "Pobbathiri", "ပုဗ္ဗသီရိ"),
                    ("Pyinmana", "Pyinmana", "ပျဉ်းမနား"),
                    ("Tatkon", "Tatkon", "တပ်ကုန်း"),
                    ("Zabuthiri", "Zabuthiri", "ဇမ္ဗူသီရိ"),
                    ("Zeyarthiri", "Zeyarthiri", "ဇေယျာသီရိ"),
                ]
            },
            {
                "code": "SGG",
                "name_en": "Sagaing Region",
                "name_my": "စစ်ကိုင်းတိုင်းဒေသကြီး",
                "townships": [
                    ("Ayadaw", "Ayadaw", "အရာတော်"),
                    ("Banmauk", "Banmauk", "ဗန်းမောက်"),
                    ("Budalin", "Budalin", "ဘုတလင်"),
                    ("Chaung-U", "Chaung-U", "ချောင်းဦး"),
                    ("Hkhamti", "Hkhamti", "ခန္တီး"),
                    ("Homalin", "Homalin", "ဟုမ္မလင်း"),
                    ("Indaw", "Indaw", "အင်းတော်"),
                    ("Kale", "Kale", "ကလေး"),
                    ("Kalewa", "Kalewa", "ကလေးဝ"),
                    ("Kanbalu", "Kanbalu", "ကန့်ဘလူ"),
                    ("Kani", "Kani", "ကနီ"),
                    ("Katha", "Katha", "ကသာ"),
                    ("Kawlin", "Kawlin", "ကောလင်း"),
                    ("Khin-U", "Khin-U", "ခင်ဦး"),
                    ("Kyunhla", "Kyunhla", "ကျွန်းလှ"),
                    ("Mawlaik", "Mawlaik", "မော်လိုက်"),
                    ("Mingin", "Mingin", "မင်းကင်း"),
                    ("Monywa", "Monywa", "မုံရွာ"),
                    ("Myaung", "Myaung", "မြောင်"),
                    ("Myinmu", "Myinmu", "မြင်းမူ"),
                    ("Pale", "Pale", "ပုလဲ"),
                    ("Paungbyin", "Paungbyin", "ဖောင်းပြင်"),
                    ("Pinlebu", "Pinlebu", "ပင်လည်ဘူး"),
                    ("Sagaing", "Sagaing", "စစ်ကိုင်း"),
                    ("Salingyi", "Salingyi", "ဆားလင်းကြီး"),
                    ("Shwebo", "Shwebo", "ရွှေဘို"),
                    ("Tabayin", "Tabayin", "ဒီပဲယင်း"),
                    ("Tamu", "Tamu", "တမူး"),
                    ("Taze", "Taze", "တန့်ဆည်"),
                    ("Tigyaing", "Tigyaing", "ထီးချိုင့်"),
                    ("Wetlet", "Wetlet", "ဝက်လက်"),
                    ("Wuntho", "Wuntho", "ဝန်းသို"),
                    ("Ye-U", "Ye-U", "ရေဦး"),
                    ("Yinmabin", "Yinmabin", "ယင်းမာပင်"),
                ]
            },
            {
                "code": "MGW",
                "name_en": "Magway Region",
                "name_my": "မကွေးတိုင်းဒေသကြီး",
                "townships": [
                    ("Aunglan", "Aunglan", "အောင်လံ"),
                    ("Chauk", "Chauk", "ချောက်"),
                    ("Gangaw", "Gangaw", "ဂန့်ဂေါ"),
                    ("Kamma", "Kamma", "ကမ္မ"),
                    ("Magway", "Magway", "မကွေး"),
                    ("Minbu", "Minbu", "မင်းဘူး"),
                    ("Mindon", "Mindon", "မင်းတုန်း"),
                    ("Minhla", "Minhla", "မင်းလှ"),
                    ("Myaing", "Myaing", "မြိုင်"),
                    ("Myothit", "Myothit", "မြို့သစ်"),
                    ("Natmauk", "Natmauk", "နတ်မောက်"),
                    ("Ngape", "Ngape", "ငဖဲ"),
                    ("Pakokku", "Pakokku", "ပခုက္ကူ"),
                    ("Pauk", "Pauk", "ပေါက်"),
                    ("Pwintbyu", "Pwintbyu", "ပွင့်ဖြူ"),
                    ("Salin", "Salin", "စလင်း"),
                    ("Saw", "Saw", "ဆော"),
                    ("Seikphyu", "Seikphyu", "ဆိပ်ဖြူ"),
                    ("Sidoktaya", "Sidoktaya", "စေတုတ္တရာ"),
                    ("Sinbaungwe", "Sinbaungwe", "ဆင်ပေါင်ဝဲ"),
                    ("Taungdwingyi", "Taungdwingyi", "တောင်တွင်းကြီး"),
                    ("Thayet", "Thayet", "သရက်"),
                    ("Tilin", "Tilin", "ထီးလင်း"),
                    ("Yenangyaung", "Yenangyaung", "ရေနံချောင်း"),
                    ("Yesagyo", "Yesagyo", "ရေစကြို"),
                ]
            },
            {
                "code": "BGO",
                "name_en": "Bago Region",
                "name_my": "ပဲခူးတိုင်းဒေသကြီး",
                "townships": [
                    ("Bago", "Bago", "ပဲခူး"),
                    ("Daik-U", "Daik-U", "ဒိုက်ဦး"),
                    ("Gyobingauk", "Gyobingauk", "ကြို့ပင်ကောက်"),
                    ("Htantabin", "Htantabin", "ထန်းတပင်"),
                    ("Kawa", "Kawa", "ကဝ"),
                    ("Kyaukkyi", "Kyaukkyi", "ကျောက်ကြီး"),
                    ("Kyauktaga", "Kyauktaga", "ကျောက်တံခါး"),
                    ("Letpadan", "Letpadan", "လက်ပံတန်း"),
                    ("Minhla", "Minhla", "မင်းလှ"),
                    ("Monyo", "Monyo", "မိုးညို"),
                    ("Natmauk", "Natmauk", "နတ်မောက်"), 
                    ("Nattalin", "Nattalin", "နတ်တလင်း"),
                    ("Nyaunglebin", "Nyaunglebin", "ညောင်လေးပင်"),
                    ("Okpho", "Okpho", "အုတ်ဖို"),
                    ("Oktwin", "Oktwin", "အုတ်တွင်း"),
                    ("Paungde", "Paungde", "ပေါင်းတည်"),
                    ("Phyu", "Phyu", "ဖြူး"),
                    ("Pyay", "Pyay", "ပြည်"),
                    ("Pyu", "Pyu", "ဖြူး"),
                    ("Shwedaung", "Shwedaung", "ရွှေတောင်"),
                    ("Shwegyin", "Shwegyin", "ရွှေကျင်"),
                    ("Taungoo", "Taungoo", "တောင်ငူ"),
                    ("Thanatpin", "Thanatpin", "သနပ်ပင်"),
                    ("Thayarwady", "Thayarwady", "သာယာဝတီ"),
                    ("Thegon", "Thegon", "သဲကုန်း"),
                    ("Waw", "Waw", "ဝေါ"),
                    ("Yedashe", "Yedashe", "ရေတာရှည်"),
                    ("Zigon", "Zigon", "ဇီးကုန်း"),
                ]
            },
            {
                "code": "AYY",
                "name_en": "Ayeyarwady Region",
                "name_my": "ဧရာဝတီတိုင်းဒေသကြီး",
                "townships": [
                    ("Bogale", "Bogale", "ဘိုကလေး"),
                    ("Danubyu", "Danubyu", "ဓနုဖြူ"),
                    ("Dedaye", "Dedaye", "ဒေးဒရဲ"),
                    ("Einme", "Einme", "အိမ်မဲ"),
                    ("Hinthada", "Hinthada", "ဟင်္သာတ"),
                    ("Ingapu", "Ingapu", "အင်္ဂပူ"),
                    ("Kangyidaunt", "Kangyidaunt", "ကန်ကြီးထောင့်"),
                    ("Kyaiklat", "Kyaiklat", "ကျိုက်လတ်"),
                    ("Kyangin", "Kyangin", "ကြံခင်း"),
                    ("Kyaunggon", "Kyaunggon", "ကျောင်းကုန်း"),
                    ("Kyonpyaw", "Kyonpyaw", "ကျုံပျော်"),
                    ("Labutta", "Labutta", "လပွတ္တာ"),
                    ("Lemyethna", "Lemyethna", "လေးမျက်နှာ"),
                    ("Maubin", "Maubin", "မအူပင်"),
                    ("Mawlamyinegyun", "Mawlamyinegyun", "မော်လမြိုင်ကျွန်း"),
                    ("Myanaung", "Myanaung", "မြန်အောင်"),
                    ("Myaungmya", "Myaungmya", "မြောင်းမြ"),
                    ("Ngapudaw", "Ngapudaw", "ငပုတော"),
                    ("Nyaungdon", "Nyaungdon", "ညောင်တုန်း"),
                    ("Pantanaw", "Pantanaw", "ပန်းတနော်"),
                    ("Pathein", "Pathein", "ပုသိမ်"),
                    ("Pyapon", "Pyapon", "ဖျာပုံ"),
                    ("Thabaung", "Thabaung", "သာပေါင်း"),
                    ("Wakema", "Wakema", "ဝါးခယ်မ"),
                    ("Yegyi", "Yegyi", "ရေကြည်"),
                    ("Zalun", "Zalun", "ဇလွန်"),
                ]
            },
            {
                "code": "TNY",
                "name_en": "Tanintharyi Region",
                "name_my": "တနင်္သာရီတိုင်းဒေသကြီး",
                "townships": [
                    ("Bokpyin", "Bokpyin", "ဘုတ်ပြင်း"),
                    ("Dawei", "Dawei", "ထားဝယ်"),
                    ("Kawthoung", "Kawthoung", "ကော့သောင်း"),
                    ("Kyunsu", "Kyunsu", "ကျွန်းစု"),
                    ("Launglon", "Launglon", "လောင်းလုံး"),
                    ("Myeik", "Myeik", "မြိတ်"),
                    ("Palaw", "Palaw", "ပုလော"),
                    ("Tanintharyi", "Tanintharyi", "တနင်္သာရီ"),
                    ("Thayetchaung", "Thayetchaung", "သရက်ချောင်း"),
                    ("Yebyu", "Yebyu", "ရေဖြူ"),
                ]
            },
            {
                "code": "MON",
                "name_en": "Mon State",
                "name_my": "မွန်ပြည်နယ်",
                "townships": [
                    ("Bilin", "Bilin", "ဘီးလင်း"),
                    ("Chaungzon", "Chaungzon", "ချောင်းဆုံ"),
                    ("Kyaikmaraw", "Kyaikmaraw", "ကျိုက်မရော"),
                    ("Kyaikto", "Kyaikto", "ကျိုက်ထို"),
                    ("Mawlamyine", "Mawlamyine", "မော်လမြိုင်"),
                    ("Mudon", "Mudon", "မုဒုံ"),
                    ("Paung", "Paung", "ပေါင်"),
                    ("Thanbyuzayat", "Thanbyuzayat", "သံဖြူဇရပ်"),
                    ("Thaton", "Thaton", "သထုံ"),
                    ("Ye", "Ye", "ရေး"),
                ]
            },
            {
                "code": "KAYIN",
                "name_en": "Kayin State",
                "name_my": "ကရင်ပြည်နယ်",
                "townships": [
                    ("Hlaingbwe", "Hlaingbwe", "လှိုင်းဘွဲ့"),
                    ("Hpa-an", "Hpa-an", "ဘားအံ"),
                    ("Hpapun", "Hpapun", "ဖာပွန်"),
                    ("Kawkareik", "Kawkareik", "ကော့ကရိတ်"),
                    ("Kyain Seikgyi", "Kyain Seikgyi", "ကြာအင်းဆိပ်ကြီး"),
                    ("Myawaddy", "Myawaddy", "မြဝတီ"),
                    ("Thandaunggyi", "Thandaunggyi", "သံတောင်ကြီး"),
                ]
            },
            {
                "code": "KACHIN",
                "name_en": "Kachin State",
                "name_my": "ကချင်ပြည်နယ်",
                "townships": [
                    ("Bhamo", "Bhamo", "ဗန်းမော်"),
                    ("Chipwi", "Chipwi", "ချီဖွေ"),
                    ("Hpakant", "Hpakant", "ဖားကန့်"),
                    ("Injangyang", "Injangyang", "အင်ဂျန်းယန်"),
                    ("Kamaing", "Kamaing", "ကာမိုင်း"),
                    ("Khaunglanhpu", "Khaunglanhpu", "ခေါင်လန်ဖူး"),
                    ("Machanbaw", "Machanbaw", "မချမ်းဘော"),
                    ("Mansi", "Mansi", "မံစီ"),
                    ("Mogaung", "Mogaung", "မိုးကောင်း"),
                    ("Mohnyin", "Mohnyin", "မိုးညှင်း"),
                    ("Momauk", "Momauk", "မိုးမောက်"),
                    ("Myitkyina", "Myitkyina", "မြစ်ကြီးနား"),
                    ("Nogmung", "Nogmung", "နောင်မွန်း"),
                    ("Puta-O", "Puta-O", "ပူတာအို"),
                    ("Shwegu", "Shwegu", "ရွှေကူ"),
                    ("Sumprabum", "Sumprabum", "ဆွမ်ပရာဘွမ်"),
                    ("Tanai", "Tanai", "တနိုင်း"),
                    ("Tsawlaw", "Tsawlaw", "ဆော့လော်"),
                    ("Waingmaw", "Waingmaw", "ဝိုင်းမော်"),
                ]
            },
            {
                "code": "KAYAH",
                "name_en": "Kayah State",
                "name_my": "ကယားပြည်နယ်",
                "townships": [
                    ("Bawlakhe", "Bawlakhe", "ဘောလခဲ"),
                    ("Demoso", "Demoso", "ဒီးမော့ဆို"),
                    ("Hpasawng", "Hpasawng", "ဖားဆောင်း"),
                    ("Hpruso", "Hpruso", "ဖရူဆို"),
                    ("Loikaw", "Loikaw", "လွိုင်ကော်"),
                    ("Mese", "Mese", "မယ်စဲ့"),
                    ("Shadaw", "Shadaw", "ရှားတော"),
                ]
            },
            {
                "code": "CHIN",
                "name_en": "Chin State",
                "name_my": "ချင်းပြည်နယ်",
                "townships": [
                    ("Falam", "Falam", "ဖလမ်း"),
                    ("Hakka", "Hakha", "ဟားခါး"),
                    ("Htantlang", "Htantlang", "ထန်တလန်"),
                    ("Kanpetlet", "Kanpetlet", "ကန်ပက်လက်"),
                    ("Madupi", "Matupi", "မတူပီ"),
                    ("Mindat", "Mindat", "မင်းတပ်"),
                    ("Paletwa", "Paletwa", "ပလက်ဝ"),
                    ("Tiddim", "Tiddim", "တီးတိန်"),
                    ("Tonzang", "Tonzang", "တွန်းဇံ"),
                ]
            },
            {
                "code": "RAKHINE",
                "name_en": "Rakhine State",
                "name_my": "ရခိုင်ပြည်နယ်",
                "townships": [
                    ("Ann", "Ann", "အမ်း"),
                    ("Buthidaung", "Buthidaung", "ဘူးသီးတောင်"),
                    ("Gwa", "Gwa", "ဂွ"),
                    ("Kyaukpyu", "Kyaukpyu", "ကျောက်ဖြူ"),
                    ("Kyauktaw", "Kyauktaw", "ကျောက်တော်"),
                    ("Maungdaw", "Maungdaw", "မောင်တော"),
                    ("Minbya", "Minbya", "မင်းပြား"),
                    ("Mrauk-U", "Mrauk-U", "မြောက်ဦး"),
                    ("Munaung", "Munaung", "မာန်အောင်"),
                    ("Myebon", "Myebon", "မြေပုံ"),
                    ("Pauktaw", "Pauktaw", "ပေါက်တော"),
                    ("Ponnagyun", "Ponnagyun", "ပုဏ္ဏားကျွန်း"),
                    ("Ramree", "Ramree", "ရမ်းဗြဲ"),
                    ("Rathedaung", "Rathedaung", "ရသေ့တောင်"),
                    ("Sittwe", "Sittwe", "စစ်တွေ"),
                    ("Thandwe", "Thandwe", "သံတွဲ"),
                    ("Toungup", "Toungup", "တောင်ကုတ်"),
                ]
            },
            {
                "code": "SHAN",
                "name_en": "Shan State",
                "name_my": "ရှမ်းပြည်နယ်",
                "townships": [
                    ("Aungban", "Aungban", "အောင်ပန်း"),
                    ("Ayetharyar", "Ayetharyar", "အေးသာယာ"),
                    ("Bawsaing", "Bawsaing", "ဘော်ဆိုင်း"),
                    ("Chinshwehaw", "Chinshwehaw", "ချင်းရွှေဟော်"),
                    ("Danu", "Danu", "ဓနု"),
                    ("Hopang", "Hopang", "ဟိုပန်"),
                    ("Hopong", "Hopong", "ဟိုပုံး"),
                    ("Hseni", "Hseni", "သိန္နီ"),
                    ("Hsipaw", "Hsipaw", "သီပေါ"),
                    ("Indaw", "Indaw", "အင်းတော်"),
                    ("Kalaw", "Kalaw", "ကလော"),
                    ("Kengtung", "Kengtung", "ကျိုင်းတုံ"),
                    ("Kunhing", "Kunhing", "ကွန်ဟိန်း"),
                    ("Kunlong", "Kunlong", "ကွမ်းလုံ"),
                    ("Kutkai", "Kutkai", "ကွတ်ခိုင်"),
                    ("Kyaukme", "Kyaukme", "ကျောက်မဲ"),
                    ("Langkho", "Langkho", "လင်းခေး"),
                    ("Lashio", "Lashio", "လားရှိုး"),
                    ("Laukkaing", "Laukkaing", "လောက်ကိုင်"),
                    ("Lawksawk", "Lawksawk", "ရပ်စောက်"),
                    ("Loilen", "Loilen", "လွိုင်လင်"),
                    ("Mabein", "Mabein", "မဘိမ်း"),
                    ("Mantong", "Mantong", "မန်တုံ"),
                    ("Mawkmai", "Mawkmai", "မောက်မယ်"),
                    ("MongHpayak", "Mong Hpayak", "မိုင်းဖြတ်"),
                    ("MongHsat", "Mong Hsat", "မိုင်းဆတ်"),
                    ("MongHsu", "Mong Hsu", "မိုင်းရှူး"),
                    ("MongKhet", "Mong Khet", "မိုင်းခတ်"),
                    ("MongKung", "Mong Kung", "မိုင်းကိုင်"),
                    ("MongNai", "Mong Nai", "မိုင်းနောင်"),
                    ("MongPan", "Mong Pan", "မိုင်းပန်"),
                    ("MongPing", "Mong Ping", "မိုင်းပျဉ်း"),
                    ("MongTon", "Mong Ton", "မိုင်းတုံ"),
                    ("MongYang", "Mong Yang", "မိုင်းယန်း"),
                    ("MongYawng", "Mong Yawng", "မိုင်းယောင်း"),
                    ("MongYai", "Mong Yai", "မိုင်းရယ်"),
                    ("Mongmit", "Mongmit", "မိုးမိတ်"),
                    ("Muse", "Muse", "မူဆယ်"),
                    ("Namhsan", "Namhsan", "နမ့်ဆန်"),
                    ("Namlan", "Namlan", "နမ့်လန်"),
                    ("Nammatu", "Nammatu", "နမ္မတူ"),
                    ("Namsang", "Namsang", "နမ့်စန်"),
                    ("Namtu", "Namtu", "နမ္မတူ"),
                    ("Nanhkan", "Nanhkan", "နမ့်ခမ်း"),
                    ("Nawnghkio", "Nawnghkio", "နောင်ချို"),
                    ("Nyaungshwe", "Nyaungshwe", "ညောင်ရွှေ"),
                    ("Pekon", "Pekon", "ဖယ်ခုံ"),
                    ("Pindaya", "Pindaya", "ပင်းတယ"),
                    ("Pinlaung", "Pinlaung", "ပင်လောင်း"),
                    ("Tachileik", "Tachileik", "တာချီလိတ်"),
                    ("Tangyan", "Tangyan", "တန့်ယန်း"),
                    ("Taunggyi", "Taunggyi", "တောင်ကြီး"),
                    ("Yaksawk", "Yaksawk", "ရပ်စောက်"),
                    ("Ywangan", "Ywangan", "ရွာငံ"),
                ]
            }
        ]

        with transaction.atomic():
            for region_data in MYANMAR_LOCATIONS:
                r_code = region_data['code']
                r_name_en = region_data['name_en']
                r_name_my = region_data['name_my']

                region, created = Region.objects.update_or_create(
                    code=r_code,
                    defaults={
                        'name_en': r_name_en,
                        'name_my': r_name_my,
                        'is_active': True,
                        'country': country
                    }
                )

                for t_data in region_data['townships']:
                    if len(t_data) >= 3:
                        t_code_suffix, t_name_en, t_name_my = t_data[:3]
                    else:
                        continue

                    full_code = f"{r_code}_{t_code_suffix.replace(' ', '')}"

                    Township.objects.update_or_create(
                        code=full_code,
                        defaults={
                            'name_en': t_name_en,
                            'name_my': t_name_my,
                            'region': region,
                            'is_active': True
                        }
                    )
        self.stdout.write('  - Region & Township: OK')

        # Supplier (sample for purchasing)
        Supplier.objects.get_or_create(code='DEFAULT', defaults={
            'name_en': 'Default Supplier', 'name_my': 'ပုံမှန်ပေးသွင်းသူ'
        })
        self.stdout.write('  - Supplier: OK')

        self.stdout.write(self.style.SUCCESS('Master data setup complete!'))
