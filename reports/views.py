from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from recovery.models import RecoveryItem
from trips.models import Trip

from .forms import TripResultForm


COMPONENT_LABELS = {
    "sleep": "수면·리듬",
    "circulation": "순환",
    "hydration": "수분",
    "skin": "피부",
}


def _score_breakdown_items(score_breakdown):
    items = []
    for key, value in score_breakdown.items():
        if isinstance(value, dict):
            detail = value.get("reason") or value.get("description") or value.get("label") or value
            score = value.get("score") or value.get("delta") or value.get("penalty")
        elif isinstance(value, (int, float)):
            detail = "예상 감점"
            score = value
        else:
            detail = value
            score = None
        magnitude = abs(score) if isinstance(score, (int, float)) else None
        items.append(
            {
                "label": COMPONENT_LABELS.get(key, key),
                "detail": detail,
                "score": score,
                "magnitude": magnitude,
            }
        )
    return items


def _component_summary(recovery_items):
    summary = {
        key: {
            "label": label,
            "planned": 0,
            "completed": 0,
            "planned_delta": 0,
            "applied_delta": 0,
        }
        for key, label in RecoveryItem.Component.choices
    }

    for item in recovery_items:
        row = summary[item.component]
        row["planned"] += 1
        row["planned_delta"] += item.score_delta
        if item.status == RecoveryItem.Status.COMPLETED:
            row["completed"] += 1
            if item.score_applied:
                row["applied_delta"] += item.score_delta

    return [row for row in summary.values() if row["planned"] > 0]


@login_required
def report_detail_view(request, trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related("origin_airport", "destination_airport"),
        pk=trip_id,
        user=request.user,
    )
    result = getattr(trip, "result", None)

    if request.method == "POST":
        if result:
            messages.info(request, "이미 리포트가 작성된 여정입니다.")
            return redirect("reports:detail", trip_id=trip.pk)

        form = TripResultForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.trip = trip
            result.save()
            if trip.status != Trip.Status.DONE:
                trip.status = Trip.Status.DONE
                trip.save(update_fields=["status", "updated_at"])
            messages.success(request, "일정 차질도가 저장되었습니다.")
            return redirect("reports:detail", trip_id=trip.pk)
    else:
        form = TripResultForm()

    recovery_items = list(RecoveryItem.objects.filter(trip=trip))
    completed_items = [
        item for item in recovery_items if item.status == RecoveryItem.Status.COMPLETED
    ]
    score_points = [
        ("예측", trip.expected_score),
        ("직후", trip.actual_score),
        ("최종", trip.current_score),
    ]
    target_progress = None
    if trip.current_score is not None and trip.target_score:
        target_progress = min(100, round((trip.current_score / trip.target_score) * 100))

    context = {
        "trip": trip,
        "result": result,
        "form": form,
        "recovery_items": recovery_items,
        "completed_count": len(completed_items),
        "total_recovery_count": len(recovery_items),
        "score_points": score_points,
        "target_progress": target_progress,
        "component_summary": _component_summary(recovery_items),
        "score_breakdown_items": _score_breakdown_items(trip.score_breakdown or {}),
    }
    return render(request, "reports/detail.html", context)

# Create your views here.
