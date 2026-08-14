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
    path("<int:trip_id>/condition/", views.daily_condition_view, name="daily_condition"),
    path("<int:trip_id>/guide/", views.before_guide_view, name="before_guide"),
    path("<int:trip_id>/items/<int:item_id>/<str:action>/", views.recovery_item_adjust, name="item_adjust"),
    path("<int:trip_id>/items/sync/", views.recovery_item_sync, name="item_sync"),
]