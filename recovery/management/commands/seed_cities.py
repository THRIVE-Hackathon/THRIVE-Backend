from django.core.management.base import BaseCommand

from trips.models import City

CITIES = [
    {"name_ko": "서울", "country_code": "KR", "timezone": "Asia/Seoul"},
    {"name_ko": "파리", "country_code": "FR", "timezone": "Europe/Paris"},
    {"name_ko": "뉴욕", "country_code": "US", "timezone": "America/New_York"},
    {"name_ko": "방콕", "country_code": "TH", "timezone": "Asia/Bangkok"},
    {"name_ko": "로스앤젤레스", "country_code": "US", "timezone": "America/Los_Angeles"},
    {"name_ko": "런던", "country_code": "GB", "timezone": "Europe/London"},
]


class Command(BaseCommand):
    help = "초기 도시 데이터를 생성합니다"

    def handle(self, *args, **options):
        created_count = 0
        for city_data in CITIES:
            city, created = City.objects.get_or_create(
                name_ko=city_data["name_ko"],
                defaults={
                    "country_code": city_data["country_code"],
                    "timezone": city_data["timezone"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"생성됨: {city.name_ko}")
            else:
                self.stdout.write(f"이미 존재함: {city.name_ko}")

        self.stdout.write(
            self.style.SUCCESS(f"완료 — 총 {created_count}개 도시 새로 생성됨")
        )