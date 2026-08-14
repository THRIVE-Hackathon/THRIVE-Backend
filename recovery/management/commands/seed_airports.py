from django.core.management.base import BaseCommand
from trips.models import Airport

AIRPORTS = [
    {"iata_code": "ICN", "name_ko": "인천국제공항", "city_name": "서울", "country_code": "KR", "timezone": "Asia/Seoul"},
    {"iata_code": "CDG", "name_ko": "샤를 드골 공항", "city_name": "파리", "country_code": "FR", "timezone": "Europe/Paris"},
    {"iata_code": "JFK", "name_ko": "존 F. 케네디 국제공항", "city_name": "뉴욕", "country_code": "US", "timezone": "America/New_York"},
    {"iata_code": "BKK", "name_ko": "수완나품 국제공항", "city_name": "방콕", "country_code": "TH", "timezone": "Asia/Bangkok"},
    {"iata_code": "LAX", "name_ko": "로스앤젤레스 국제공항", "city_name": "로스앤젤레스", "country_code": "US", "timezone": "America/Los_Angeles"},
    {"iata_code": "LHR", "name_ko": "히스로 공항", "city_name": "런던", "country_code": "GB", "timezone": "Europe/London"},
    {"iata_code": "MXP", "name_ko": "말펜사 공항", "city_name": "밀라노", "country_code": "IT", "timezone": "Europe/Rome"},
]


class Command(BaseCommand):
    help = "초기 공항 데이터를 생성합니다"

    def handle(self, *args, **options):
        for a in AIRPORTS:
            obj, created = Airport.objects.get_or_create(
                iata_code=a["iata_code"],
                defaults={k: v for k, v in a.items() if k != "iata_code"},
            )
            self.stdout.write(f"{'생성됨' if created else '이미 존재함'}: {obj}")