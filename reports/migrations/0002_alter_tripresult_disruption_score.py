# Generated manually to align the disruption survey with the final report design.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tripresult",
            name="disruption_score",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "문제 없음"),
                    (1, "대부분의 일정 수행"),
                    (2, "절반 정도 수행"),
                    (3, "대부분의 일정 취소"),
                ],
                verbose_name="일정 차질도",
            ),
        ),
    ]
