from django.db import models

from trips.models import Trip


class TripResult(models.Model):
    class DisruptionScore(models.IntegerChoices):
        NONE = 0, "평소처럼 다 했어요"
        MILD = 1, "힘들었지만 계획대로 했어요"
        REDUCED = 2, "일부를 줄이거나 짧게 했어요"
        DELAYED = 3, "하루치 일정을 미뤘어요"
        LOST_DAY = 4, "하루를 통째로 쉬었어요"
        MAJOR_LOSS = 5, "이틀 이상 영향을 받았어요"

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
