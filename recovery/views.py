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
from common.services.recovery import CHECK_TYPE_INPUT_MODE, get_inflight_tips, get_layover_tips, RECOVERY_ITEM_CATALOG
from common.services.score import clamp_score
from common.services.timezone import to_timezone
from trips.services import refresh_trip_status

@login_required
def inflight_check_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

    checks = {}
    for check_type, label in InflightCheck.CheckType.choices:
        obj, _ = InflightCheck.objects.get_or_create(
            trip=trip, check_type=check_type, defaults={"count": 0}
        )
        checks[check_type] = obj

    context = {"trip": trip, "checks": checks, "input_modes": CHECK_TYPE_INPUT_MODE}
    return render(request, "recovery/inflight_check.html", context)


@login_required
def inflight_check_adjust(request, trip_id, check_type, action):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    check, _ = InflightCheck.objects.get_or_create(
        trip=trip, check_type=check_type, defaults={"count": 0}
    )

    input_mode = CHECK_TYPE_INPUT_MODE.get(check_type, "counter")

    if input_mode == "toggle":
        check.count = 0 if check.count > 0 else 1
    else:
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
        InflightCheck.objects.filter(pk=check.pk).update(
            count=F("count") + delta, client_event_id=batch_id, synced_at=timezone.now()
        )
        check.refresh_from_db()

        if check.count < 0:
            check.count = 0
        if CHECK_TYPE_INPUT_MODE.get(check_type) == "toggle" and check.count > 1:
            check.count = 1  # 토글은 0 또는 1만 허용

        check.save(update_fields=["count"])
        updated_counts[check_type] = check.count

    return JsonResponse({"counts": updated_counts})

DAILY_RECOVERY_LIMIT = 15

CONDITION_CHOICES = [
    (5, "매우 좋음"),
    (4, "좋음"),
    (3, "보통"),
    (2, "피곤함"),
    (1, "매우 피곤함"),
]


@login_required
def daily_condition_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    today_local = to_timezone(timezone.now(), trip.destination_airport.timezone).date()

    if request.method == "POST":
        score = request.POST.get("score")
        if score and score.isdigit() and 1 <= int(score) <= 5:
            DailyCondition.objects.update_or_create(
                trip=trip,
                local_date=today_local,
                defaults={"score": int(score)},
            )
            messages.success(request, "오늘의 컨디션이 기록됐어요")
            return redirect("trips:home")
        messages.error(request, "컨디션을 선택해주세요")

    existing = DailyCondition.objects.filter(trip=trip, local_date=today_local).first()
    context = {
        "trip": trip,
        "choices": CONDITION_CHOICES,
        "existing": existing,
    }
    return render(request, "recovery/daily_condition.html", context)

@login_required
def before_guide_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    context = {
        "trip": trip,
        "inflight_tips": get_inflight_tips(),
        "layover_tips": get_layover_tips(),
    }
    return render(request, "recovery/before_guide.html", context)

@login_required
def recovery_item_adjust(request, trip_id, item_id, action):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    item = get_object_or_404(RecoveryItem, pk=item_id, trip=trip)
    mode = RECOVERY_ITEM_CATALOG.get(item.key, {}).get("mode", "toggle")

    applied_today = (
        RecoveryItem.objects.filter(trip=trip, local_date=item.local_date, score_applied=True)
        .aggregate(total=Sum("score_delta"))["total"]
        or 0
    )

    if mode == "toggle":
        if item.status == RecoveryItem.Status.PENDING:
            item.status = RecoveryItem.Status.COMPLETED
            item.completed_at = timezone.now()
            if applied_today + item.score_delta <= DAILY_RECOVERY_LIMIT:
                item.score_applied = True
                trip.current_score = clamp_score((trip.current_score or 0) + item.score_delta)
                trip.save(update_fields=["current_score"])
            else:
                messages.info(request, "오늘은 충분히 하셨어요")
        else:
            item.status = RecoveryItem.Status.PENDING
            item.completed_at = None
            if item.score_applied:
                trip.current_score = clamp_score((trip.current_score or 0) - item.score_delta)
                trip.save(update_fields=["current_score"])
            item.score_applied = False
        item.save()

    else:  # counter
        if action == "increment":
            if applied_today + item.score_delta <= DAILY_RECOVERY_LIMIT:
                item.count += 1
                trip.current_score = clamp_score((trip.current_score or 0) + item.score_delta)
                trip.save(update_fields=["current_score"])
                item.score_applied = True
            else:
                messages.info(request, "오늘은 충분히 하셨어요")
        elif action == "decrement" and item.count > 0:
            item.count -= 1
            trip.current_score = clamp_score((trip.current_score or 0) - item.score_delta)
            trip.save(update_fields=["current_score"])
            if item.count == 0:
                item.score_applied = False
        item.save()

    return redirect("trips:home")

@login_required
@require_POST
def recovery_item_sync(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    try:
        payload = json.loads(request.body)
        deltas = payload.get("deltas", {})  # {item_id: delta}
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "invalid payload"}, status=400)

    applied_today = (
        RecoveryItem.objects.filter(trip=trip, local_date=timezone.localdate(), score_applied=True)
        .aggregate(total=Sum("score_delta"))["total"]
        or 0
    )

    results = {}
    for item_id_str, delta in deltas.items():
        if not isinstance(delta, int) or delta == 0:
            continue
        try:
            item = RecoveryItem.objects.get(pk=int(item_id_str), trip=trip)
        except (RecoveryItem.DoesNotExist, ValueError):
            continue

        mode = RECOVERY_ITEM_CATALOG.get(item.key, {}).get("mode", "toggle")

        if mode == "toggle":
            is_checked = delta > 0
            item.status = RecoveryItem.Status.COMPLETED if is_checked else RecoveryItem.Status.PENDING
            item.completed_at = timezone.now() if is_checked else None
        else:
            item.count = max(0, item.count + delta)

        if applied_today + item.score_delta <= DAILY_RECOVERY_LIMIT:
            was_applied = item.score_applied
            item.score_applied = (mode == "toggle" and item.status == RecoveryItem.Status.COMPLETED) or (
                mode == "counter" and item.count > 0
            )
            if item.score_applied and not was_applied:
                trip.current_score = clamp_score((trip.current_score or 0) + item.score_delta)
                applied_today += item.score_delta
            elif not item.score_applied and was_applied:
                trip.current_score = clamp_score((trip.current_score or 0) - item.score_delta)
                applied_today -= item.score_delta

        item.save()
        results[str(item.id)] = {"status": item.status, "count": item.count}

    trip.save(update_fields=["current_score"])
    return JsonResponse({"items": results, "current_score": trip.current_score})
