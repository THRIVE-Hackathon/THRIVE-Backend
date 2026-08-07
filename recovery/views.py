from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from trips.models import Trip
from .models import InflightCheck, RecoveryItem, DailyCondition
import json
from django.db.models import F, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from common.services.recovery import generate_recovery_items, get_layover_guide
from common.services.score import clamp_score
from common.services.timezone import to_timezone

@login_required
def inflight_check_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

    checks = {}
    for check_type, label in InflightCheck.CheckType.choices:
        obj, _ = InflightCheck.objects.get_or_create(
            trip=trip, check_type=check_type, defaults={"count": 0}
        )
        checks[check_type] = obj

    context = {"trip": trip, "checks": checks}
    return render(request, "recovery/inflight_check.html", context)


@login_required
def inflight_check_adjust(request, trip_id, check_type, action):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    check, _ = InflightCheck.objects.get_or_create(
        trip=trip, check_type=check_type, defaults={"count": 0}
    )
    if action == "increment":
        check.count += 1
    elif action == "decrement":
        check.count = max(0, check.count - 1)
    check.save()
    return redirect("recovery:inflight_check", trip_id=trip.pk)

@login_required
@require_POST
def inflight_check_sync(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    try:
        payload = json.loads(request.body)
        deltas = payload.get("deltas", {})
        batch_id = payload.get("client_event_id", "")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "invalid payload"}, status=400)

    valid_types = dict(InflightCheck.CheckType.choices)
    updated_counts = {}

    for check_type, delta in deltas.items():
        if check_type not in valid_types or not isinstance(delta, int) or delta == 0:
            continue
        check, _ = InflightCheck.objects.get_or_create(
            trip=trip, check_type=check_type, defaults={"count": 0}
        )
        # F()로 반영해서 동시 요청 시 race condition 방지
        InflightCheck.objects.filter(pk=check.pk).update(
            count=F("count") + delta,
            client_event_id=batch_id,
            synced_at=timezone.now(),
        )
        check.refresh_from_db()
        # 음수 방지 (혹시 delta가 과도하게 마이너스로 쌓였을 경우)
        if check.count < 0:
            check.count = 0
            check.save(update_fields=["count"])
        updated_counts[check_type] = check.count

    return JsonResponse({"counts": updated_counts})

DAILY_RECOVERY_LIMIT = 15

@login_required
def recovery_plan_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    items = generate_recovery_items(trip)

    now = timezone.now()
    upcoming = [item for item in items if item.status == RecoveryItem.Status.PENDING]
    current_item = upcoming[0] if upcoming else None

    context = {"trip": trip, "items": items, "current_item": current_item}
    return render(request, "recovery/plan.html", context)


@login_required
def recovery_check_toggle(request, trip_id, item_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    item = get_object_or_404(RecoveryItem, pk=item_id, trip=trip)

    if item.status == RecoveryItem.Status.PENDING:
        applied_today = (
            RecoveryItem.objects.filter(
                trip=trip, local_date=item.local_date, score_applied=True
            ).aggregate(total=Sum("score_delta"))["total"]
            or 0
        )

        item.status = RecoveryItem.Status.COMPLETED
        item.completed_at = timezone.now()

        if applied_today + item.score_delta <= DAILY_RECOVERY_LIMIT:
            item.score_applied = True
            trip.current_score = clamp_score((trip.current_score or 0) + item.score_delta)
            trip.save(update_fields=["current_score"])
        else:
            item.score_applied = False
            messages.info(request, "오늘은 충분히 하셨어요")
        item.save()
    else:
        item.status = RecoveryItem.Status.PENDING
        item.completed_at = None
        if item.score_applied:
            trip.current_score = clamp_score((trip.current_score or 0) - item.score_delta)
            trip.save(update_fields=["current_score"])
        item.score_applied = False
        item.save()

    return redirect("recovery:plan", trip_id=trip.pk)

CONDITION_CHOICES = [
    (5, "아주 좋아요"),
    (4, "좋아요"),
    (3, "보통이에요"),
    (2, "피곤해요"),
    (1, "많이 피곤해요"),
]


@login_required
def daily_condition_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    today_local = to_timezone(timezone.now(), trip.destination_city.timezone).date()

    if request.method == "POST":
        score = request.POST.get("score")
        if score and score.isdigit() and 1 <= int(score) <= 5:
            DailyCondition.objects.update_or_create(
                trip=trip,
                local_date=today_local,
                defaults={"score": int(score)},
            )
            messages.success(request, "오늘의 컨디션이 기록됐어요")
            return redirect("recovery:plan", trip_id=trip.pk)
        messages.error(request, "컨디션을 선택해주세요")

    existing = DailyCondition.objects.filter(trip=trip, local_date=today_local).first()
    context = {
        "trip": trip,
        "choices": CONDITION_CHOICES,
        "existing": existing,
    }
    return render(request, "recovery/daily_condition.html", context)

@login_required
def layover_guide_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    guide = get_layover_guide(trip.max_layover_minutes)
    context = {"trip": trip, "guide": guide}
    return render(request, "recovery/layover_guide.html", context)