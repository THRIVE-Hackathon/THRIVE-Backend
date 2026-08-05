from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("<int:trip_id>/", views.report_detail_view, name="detail"),
]
