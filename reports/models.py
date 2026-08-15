from django.db import models

from trips.models import Trip


class TripResult(models.Model):
    class DisruptionScore(models.IntegerChoices):
        NONE = 0, "문제 없음"
        MOST_DONE = 1, "대부분의 일정 수행"
        HALF_DONE = 2, "절반 정도 수행"
        MOST_CANCELLED = 3, "대부분의 일정 취소"

    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name="result",
        verbose_name="여정",
    )
    disruption_score = models.PositiveSmallIntegerField(
        "일정 차질도",
        choices=DisruptionScore.choices,
    )
    selected_answer = models.CharField("선택 답변", max_length=120)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "여정 결과"
        verbose_name_plural = "여정 결과"

    def __str__(self):
        return f"{self.trip} / 차질도 {self.disruption_score}"

# Create your models here.
