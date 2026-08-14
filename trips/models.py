from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


class Airport(models.Model):
    iata_code = models.CharField("공항 코드", max_length=4, unique=True)  # 예: ICN
    name_ko = models.CharField("공항명", max_length=80)  # 예: 인천국제공항
    city_name = models.CharField("도시명", max_length=80)  # 예: 서울
    country_code = models.CharField("국가 코드", max_length=2)
    timezone = models.CharField("시간대", max_length=80)
    active = models.BooleanField("사용 여부", default=True)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)

    class Meta:
        ordering = ["city_name"]
        verbose_name = "공항"
        verbose_name_plural = "공항"

    def __str__(self):
        return f"{self.iata_code} {self.name_ko}"

    @property
    def display_label(self):
        return f"{self.iata_code} {self.name_ko}"


class Trip(models.Model):
    class LayoverCount(models.TextChoices):
        NONE = "none", "없음"
        ONE = "one", "1회"
        TWO_PLUS = "two_plus", "2회 이상"

    class Direction(models.TextChoices):
        EAST = "east", "동행"
        WEST = "west", "서행"
        NONE = "none", "시차 없음"

    class Status(models.TextChoices):
        CREATED = "created", "등록됨"
        LANDED = "landed", "착륙함"
        RECOVERING = "recovering", "회복 중"
        DONE = "done", "완료"

    ACTIVE_STATUSES = [Status.CREATED, Status.LANDED, Status.RECOVERING]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="사용자",
    )
    origin_airport = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="origin_trips",
        verbose_name="출발 공항",
    )
    destination_airport = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="destination_trips",
        verbose_name="도착 공항",
    )
    layover_count = models.CharField(
        "경유 횟수",
        max_length=20,
        choices=LayoverCount.choices,
        default=LayoverCount.NONE,
    )
    total_flight_minutes = models.PositiveIntegerField("총 비행시간")
    total_elapsed_minutes = models.PositiveIntegerField(
        "총 경과시간",
        null=True,
        blank=True,
    )
    max_layover_minutes = models.PositiveIntegerField(
        "최장 대기시간",
        null=True,
        blank=True,
    )
    timezone_diff_minutes = models.IntegerField("시차", null=True, blank=True)
    travel_direction = models.CharField(
        "이동 방향",
        max_length=10,
        choices=Direction.choices,
        default=Direction.NONE,
    )
    landing_at = models.DateTimeField("착륙 시각", null=True, blank=True)
    next_schedule_at = models.DateTimeField("다음 일정 시각", null=True, blank=True)
    next_schedule_after_minutes = models.PositiveIntegerField("다음 일정까지")
    status = models.CharField(
        "상태",
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )
    expected_score = models.PositiveSmallIntegerField("예상 점수", null=True, blank=True)
    actual_score = models.PositiveSmallIntegerField("실측 점수", null=True, blank=True)
    current_score = models.PositiveSmallIntegerField("현재 점수", null=True, blank=True)
    target_score = models.PositiveSmallIntegerField("목표 점수", null=True, blank=True)
    score_breakdown = models.JSONField("점수 근거", default=dict, blank=True)
    summary_text = models.CharField("요약 문구", max_length=255, blank=True)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)
    updated_at = models.DateTimeField("수정 시각", auto_now=True)
    departure_at = models.DateTimeField("출발 시각", null=True, blank=True)
    arrival_at = models.DateTimeField("도착 예정 시각", null=True, blank=True)

    has_recent_flight_experience = models.BooleanField("장거리 비행 경험 여부", null=True, blank=True)
    last_flight_date = models.DateField("마지막 비행 일자", null=True, blank=True)
    last_flight_minutes = models.PositiveIntegerField("마지막 비행 총 시간(분)", null=True, blank=True)
    survey_skipped = models.BooleanField("설문 건너뛰기 여부", default=False)

    class TypicalImpact(models.TextChoices):
        NONE = "none", "아무런 영향 없음"
        QUICK_RECOVERY = "quick", "도착 직후 회복됨"
        SLIGHT_FATIGUE = "slight", "살짝 피로함"
        SCHEDULE_IMPACT = "schedule", "일정에 영향 줌"

    typical_impact = models.CharField(
        "평소 컨디션 영향도", max_length=20, choices=TypicalImpact.choices, blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status__in=["created", "landed", "recovering"]),
                name="uniq_active_trip_per_user",
            )
        ]
        verbose_name = "여정"
        verbose_name_plural = "여정"

    def __str__(self):
        return f"{self.origin_airport} -> {self.destination_airport}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_report_required(self):
        return self.status == self.Status.DONE and not hasattr(self, "result")

    @property
    def route_name(self):
        return f"{self.origin_airport.iata_code} → {self.destination_airport.iata_code}"

    def get_absolute_url(self):
        return reverse("reports:detail", kwargs={"trip_id": self.pk})

# Create your models here.
