from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


class City(models.Model):
    name_ko = models.CharField("도시명", max_length=80)
    country_code = models.CharField("국가 코드", max_length=2)
    timezone = models.CharField("시간대", max_length=80)
    active = models.BooleanField("사용 여부", default=True)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)

    class Meta:
        ordering = ["name_ko"]
        verbose_name = "도시"
        verbose_name_plural = "도시"

    def __str__(self):
        return self.name_ko


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
    origin_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="origin_trips",
        verbose_name="출발지",
    )
    destination_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="destination_trips",
        verbose_name="도착지",
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
        return f"{self.origin_city} -> {self.destination_city}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_report_required(self):
        return self.status == self.Status.DONE and not hasattr(self, "result")

    @property
    def route_name(self):
        return f"{self.origin_city.name_ko} -> {self.destination_city.name_ko}"

    def get_absolute_url(self):
        return reverse("reports:detail", kwargs={"trip_id": self.pk})

# Create your models here.
