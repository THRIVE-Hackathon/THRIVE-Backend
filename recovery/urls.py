from django.urls import path

from . import views

app_name = "recovery"

urlpatterns = [
    path("<int:trip_id>/checks/", views.inflight_check_view, name="inflight_check"),
    path(
        "<int:trip_id>/checks/<str:check_type>/<str:action>/",
        views.inflight_check_adjust,
        name="inflight_check_adjust",
    ),
    path("<int:trip_id>/checks/sync/", views.inflight_check_sync, name="inflight_check_sync"),
    path("<int:trip_id>/plan/", views.recovery_plan_view, name="plan"),
    path("<int:trip_id>/items/<int:item_id>/toggle/", views.recovery_check_toggle, name="item_toggle"),
    path("<int:trip_id>/condition/", views.daily_condition_view, name="daily_condition"),
    path("<int:trip_id>/layover/", views.layover_guide_view, name="layover_guide"),
]