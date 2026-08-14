from django.contrib import admin

from .models import Airport, Trip


@admin.register(Airport)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name_ko", "country_code", "timezone", "active"]
    list_filter = ["active", "country_code"]
    search_fields = ["name_ko", "country_code", "timezone"]


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "origin_airport",
        "destination_airport",
        "status",
        "expected_score",
        "actual_score",
        "current_score",
        "created_at",
    ]
    list_filter = ["status", "layover_count", "travel_direction"]
    search_fields = ["user__email", "origin_airport__name_ko", "destination_airport__name_ko"]

# Register your models here.
