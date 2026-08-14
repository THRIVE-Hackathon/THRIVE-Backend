from django.db import models

from trips.models import Trip


class InflightCheck(models.Model):
    class CheckType(models.TextChoices):
        WATER = "water", "물 마심"
        STRETCH = "stretch", "스트레칭"
        MOISTURIZE = "moisturize", "보습"
        SLEEP = "sleep", "6시간 취침하기"

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="inflight_checks",
        verbose_name="여정",
    )
    check_type = models.CharField("체크 유형", max_length=30, choices=CheckType.choices)
    count = models.PositiveSmallIntegerField("횟수", default=0)
    client_event_id = models.CharField("클라이언트 이벤트 ID", max_length=80, blank=True)
    occurred_at = models.DateTimeField("발생 시각", null=True, blank=True)
    synced_at = models.DateTimeField("동기화 시각", null=True, blank=True)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)
    updated_at = models.DateTimeField("수정 시각", auto_now=True)

    class Meta:
        verbose_name = "기내 체크"
        verbose_name_plural = "기내 체크"

    def __str__(self):
        return f"{self.trip} / {self.get_check_type_display()} x{self.count}"


class RecoveryItem(models.Model):
    class Component(models.TextChoices):
        SLEEP = "sleep", "수면"
        CIRCULATION = "circulation", "순환"
        HYDRATION = "hydration", "수분"
        SKIN = "skin", "피부"

    class Status(models.TextChoices):
        PENDING = "pending", "미완료"
        COMPLETED = "completed", "완료"

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="recovery_items",
        verbose_name="여정",
    )
    title = models.CharField("항목명", max_length=100)
    key = models.CharField("항목 키", max_length=30, blank=True)  
    count = models.PositiveSmallIntegerField("카운트", default=0)
    component = models.CharField("요소", max_length=20, choices=Component.choices)
    scheduled_at = models.DateTimeField("예정 시각")
    local_date = models.DateField("현지 날짜")
    score_delta = models.DecimalField("상승 점수", max_digits=4, decimal_places=2)
    reason_text = models.CharField("이유 문구", max_length=255, blank=True)
    status = models.CharField(
        "상태",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField("완료 시각", null=True, blank=True)
    score_applied = models.BooleanField("점수 반영 여부", default=False)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)
    updated_at = models.DateTimeField("수정 시각", auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]
        verbose_name = "회복 항목"
        verbose_name_plural = "회복 항목"

    def __str__(self):
        return f"{self.title} ({self.trip})"


class DailyCondition(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="daily_conditions",
        verbose_name="여정",
    )
    local_date = models.DateField("현지 날짜")
    score = models.PositiveSmallIntegerField("컨디션 점수")
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trip", "local_date"],
                name="uniq_daily_condition_per_trip_date",
            )
        ]
        ordering = ["-local_date"]
        verbose_name = "하루 컨디션"
        verbose_name_plural = "하루 컨디션"

    def __str__(self):
        return f"{self.trip} / {self.local_date}: {self.score}"

# Create your models here.
