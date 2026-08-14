from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trip_list_view, name="list"),
    path("<int:trip_id>/calendar.ics", views.trip_calendar_view, name="calendar"),
    path("new/", views.trip_create_step1_view, name="create_step1"),
    path("new/step2/", views.trip_create_step2_view, name="create_step2"),
    path("<int:trip_id>/survey/", views.trip_survey_view, name="survey"),
    path("<int:trip_id>/survey/skip/", views.trip_survey_skip_view, name="survey_skip"),
    path("home/", views.trip_home_view, name="home"),
    path("new/cancel/", views.trip_registration_cancel_view, name="registration_cancel"),
    path("<int:trip_id>/start-recovery/", views.trip_start_recovery_view, name="start_recovery"),
    path("<int:trip_id>/edit/", views.trip_edit_start_view, name="edit_start"),
]   
