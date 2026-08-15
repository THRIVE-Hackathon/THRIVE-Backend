# Generated manually to align profile age storage with the final signup design.

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


AGE_GROUP_TO_AGE = {
    "teens": 19,
    "twenties_early": 24,
    "twenties_late": 28,
    "thirties": 35,
    "forties_plus": 40,
}


def forwards(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    for profile in Profile.objects.all().only("id", "age_group").iterator():
        profile.age = AGE_GROUP_TO_AGE.get(profile.age_group, 28)
        profile.save(update_fields=["age"])


def backwards(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    for profile in Profile.objects.all().only("id", "age").iterator():
        if profile.age < 20:
            profile.age_group = "teens"
        elif profile.age < 25:
            profile.age_group = "twenties_early"
        elif profile.age < 30:
            profile.age_group = "twenties_late"
        elif profile.age < 40:
            profile.age_group = "thirties"
        else:
            profile.age_group = "forties_plus"
        profile.save(update_fields=["age_group"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="age_group",
            field=models.CharField(
                blank=True,
                choices=[
                    ("teens", "10대"),
                    ("twenties_early", "20대 초반"),
                    ("twenties_late", "20대 후반"),
                    ("thirties", "30대"),
                    ("forties_plus", "40대 이상"),
                ],
                max_length=30,
                null=True,
                verbose_name="연령대",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="age",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(1), MaxValueValidator(120)],
                verbose_name="나이",
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="profile",
            name="age",
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(120)],
                verbose_name="나이",
            ),
        ),
        migrations.RemoveField(
            model_name="profile",
            name="age_group",
        ),
    ]
