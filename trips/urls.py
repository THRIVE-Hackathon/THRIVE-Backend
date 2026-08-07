from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trip_list_view, name="list"),
    path("<int:trip_id>/calendar.ics", views.trip_calendar_view, name="calendar"),
    path("new/", views.trip_create_view, name="create"),
    path("<int:trip_id>/score/", views.trip_expected_score_view, name="expected_score"),
    path("<int:trip_id>/actual-score/", views.trip_actual_score_view, name="actual_score"),
]
