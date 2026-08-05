from django.contrib import admin

from .models import TripResult


@admin.register(TripResult)
class TripResultAdmin(admin.ModelAdmin):
    list_display = ["trip", "disruption_score", "created_at"]
    list_filter = ["disruption_score"]
    search_fields = ["trip__user__email"]

# Register your models here.
