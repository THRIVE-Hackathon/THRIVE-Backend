from django.contrib import admin

from .models import DailyCondition, InflightCheck, RecoveryItem


@admin.register(InflightCheck)
class InflightCheckAdmin(admin.ModelAdmin):
    list_display = ["trip", "check_type", "count", "occurred_at", "synced_at"]
    list_filter = ["check_type"]


@admin.register(RecoveryItem)
class RecoveryItemAdmin(admin.ModelAdmin):
    list_display = ["trip", "title", "component", "score_delta", "status", "scheduled_at"]
    list_filter = ["component", "status"]
    search_fields = ["title", "trip__user__email"]


@admin.register(DailyCondition)
class DailyConditionAdmin(admin.ModelAdmin):
    list_display = ["trip", "local_date", "score", "created_at"]

# Register your models here.
