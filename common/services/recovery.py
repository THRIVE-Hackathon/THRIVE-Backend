from datetime import timedelta

from django.utils import timezone as dj_timezone
from django.utils import timezone
from common.ai.summaries import get_recovery_item_reason
from .timezone import to_timezone

from concurrent.futures import ThreadPoolExecutor

RECOVERY_ITEM_CATALOG = {
    "moisturize": {"title": "피부 보습하기", "component": "skin", "score_delta": 3, "mode": "toggle"},
    "sleep_6h": {"title": "6시간 취침하기", "component": "sleep", "score_delta": 5, "mode": "toggle"},
    "walk_light": {"title": "가볍게 산책하기", "component": "circulation", "score_delta": 4, "mode": "toggle"},
    "sunlight": {"title": "햇빛 쬐기", "component": "sleep", "score_delta": 4, "mode": "toggle"},
    "water": {"title": "물 100ml 마시기", "component": "hydration", "score_delta": 1, "mode": "counter"},
    "stretch": {"title": "팔·다리 스트레칭하기", "component": "circulation", "score_delta": 2, "mode": "counter"},
}

CHECK_TYPE_INPUT_MODE = {
    "water": "counter",
    "stretch": "counter",
    "moisturize": "toggle",
    "sleep": "toggle",
}

INFLIGHT_TIPS = [
    {"title": "스트레칭", "desc": "순환을 돕고, 장시간 착석으로 굳은 다리를 풀어줘요.", "component": "순환"},
    {"title": "물 섭취", "desc": "기내 건조한 환경으로 손실된 수분을 보충하세요.", "component": "수분"},
    {"title": "마스크팩", "desc": "장시간 붙어있지 않도록 유의해야 돼요.", "component": "피부"},
]


def get_inflight_tips():
    return INFLIGHT_TIPS


def get_layover_tips():
    # 기존 LAYOVER_GUIDE_CATALOG의 구간 분기를 없애고 고정 목록으로 단순화
    return [
        {"title": "터미널 산책", "desc": "순환을 돕고, 장시간 착석으로 굳은 다리를 풀어줘요.", "component": "순환"},
        {"title": "물 섭취", "desc": "기내 건조한 환경으로 손실된 수분을 보충하세요.", "component": "수분"},
        {"title": "세면대 보습", "desc": "얼굴과 손에 수분을 공급해 피부 장벽을 지켜요.", "component": "피부"},
        {"title": "10분 이상 서 있기", "desc": "서 있는 것만으로도 혈액 순환에 도움이 돼요.", "component": "순환"},
    ]

def _next_slot_for_component(current_local, component, direction):
    """카테고리별 배치 규칙에 맞는 다음 슬롯을 반환한다."""
    if component == "sleep":
        # 현지 22~07시에만 배치 (기능명세서 규칙 3)
        candidate = current_local.replace(hour=22, minute=0, second=0, microsecond=0)
        if current_local.hour >= 22:
            candidate += timedelta(days=1)
        elif current_local.hour < 7:
            candidate = current_local.replace(hour=6, minute=0, second=0, microsecond=0)
        return candidate

    if component == "circulation" and RECOVERY_ITEM_CATALOG[component]["title"] == "광 노출 30분":
        # (실제로는 sleep 카테고리가 광노출이라 이 분기는 안 타지만 방어적으로 남김
        pass

    return current_local + timedelta(hours=4)


def generate_recovery_items(trip):
    from recovery.models import RecoveryItem

    if trip.recovery_items.exists():
        return list(trip.recovery_items.all())

    remaining = trip.next_schedule_after_minutes or 0
    max_recovery_minutes = min(remaining, 3 * 24 * 60)
    total_count = min(12, remaining // 240)
    if total_count <= 0:
        return []

    breakdown = trip.score_breakdown or {}
    ordered_components = sorted(breakdown.keys(), key=lambda component: breakdown[component])
    if not ordered_components:
        ordered_components = ["sleep", "circulation", "hydration", "skin"]

    dest_tz = trip.destination_airport.timezone
    now_local = to_timezone(dj_timezone.now(), dest_tz)
    slot = now_local

    items = []
    for i in range(total_count):
        component = ordered_components[i % len(ordered_components)]
        catalog_entry = RECOVERY_ITEM_CATALOG[component]

        if component == "sleep":
            slot = _next_slot_for_component(slot, "sleep", trip.travel_direction)
            title = "광 노출 30분" if trip.travel_direction != "none" else catalog_entry["title"]
            if trip.travel_direction == "east":
                slot = slot.replace(hour=9, minute=0)
            elif trip.travel_direction == "west":
                slot = slot.replace(hour=15, minute=0)
        else:
            slot = slot + timedelta(hours=4)
            title = catalog_entry["title"]

        items.append(
            RecoveryItem(
                trip=trip,
                title=title,
                component=component,
                scheduled_at=slot.astimezone(dj_timezone.utc),
                local_date=slot.date(),
                score_delta=catalog_entry["score_delta"],
            )
        )

    # 여기서부터가 바뀐 부분: 순차 호출 대신 동시에 쏘고 기다리기
    with ThreadPoolExecutor(max_workers=6) as executor:
        reasons = list(executor.map(get_recovery_item_reason, items))
    for item, reason in zip(items, reasons):
        item.reason_text = reason

    RecoveryItem.objects.bulk_create(items)
    return list(trip.recovery_items.all())


def get_or_create_recovery_items(trip):
    from recovery.models import RecoveryItem

    if trip.recovery_items.exists():
        return list(trip.recovery_items.all())

    items = [
        RecoveryItem(
            trip=trip,
            key=key,
            title=entry["title"],
            component=entry["component"],
            score_delta=entry["score_delta"],
            local_date=timezone.localdate(),
        )
        for key, entry in RECOVERY_ITEM_CATALOG.items()
    ]
    RecoveryItem.objects.bulk_create(items)
    return list(trip.recovery_items.all())