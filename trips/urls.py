from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trip_list_view, name="list"),
    path("<int:trip_id>/calendar.ics", views.trip_calendar_view, name="calendar"),
]
