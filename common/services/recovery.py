from datetime import timedelta

from django.utils import timezone as dj_timezone

from .timezone import to_timezone

RECOVERY_ITEM_CATALOG = {
    "sleep": {"title": "광 노출 30분", "score_delta": 5},
    "circulation": {"title": "10분 걷기", "score_delta": 4},
    "hydration": {"title": "물 500ml", "score_delta": 3},
    "skin": {"title": "보습", "score_delta": 3},
}


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
    """Trip에 대해 회복 항목을 생성한다. 이미 항목이 있으면 새로 만들지 않는다."""
    from recovery.models import RecoveryItem  # 순환 import 방지용 지연 import

    if trip.recovery_items.exists():
        return list(trip.recovery_items.all())

    remaining = trip.next_schedule_after_minutes or 0
    total_count = min(12, remaining // 240)  # 규칙 1: 4시간당 1개, 최대 12개
    if total_count <= 0:
        return []

    breakdown = trip.score_breakdown or {}
    # 규칙 2: 감점 큰 요소부터 배치 (가장 낮은 값 = 가장 큰 감점)
    ordered_components = sorted(
        breakdown.keys(), key=lambda component: breakdown[component]
    )
    if not ordered_components:
        ordered_components = ["sleep", "circulation", "hydration", "skin"]

    dest_tz = trip.destination_city.timezone
    now_local = to_timezone(dj_timezone.now(), dest_tz)
    slot = now_local

    items = []
    for i in range(total_count):
        component = ordered_components[i % len(ordered_components)]
        catalog_entry = RECOVERY_ITEM_CATALOG[component]

        if component == "sleep":
            slot = _next_slot_for_component(slot, "sleep", trip.travel_direction)
            title = "광 노출 30분" if trip.travel_direction != "none" else catalog_entry["title"]
            # 규칙 4: 동행이면 오전, 서행이면 오후에 광 노출 배치
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

    RecoveryItem.objects.bulk_create(items)
    return list(trip.recovery_items.all())

LAYOVER_GUIDE_CATALOG = {
    "short": {
        "label": "1~3시간 대기",
        "items": [
            {"title": "터미널 걷기 15분", "desc": "순환 회복에 가장 효과적입니다. 좌석에서 일어나 천천히", "component": "순환"},
            {"title": "물 500ml 마시기", "desc": "기내 저습도로 손실된 수분을 보충합니다.", "component": "수분"},
            {"title": "세면대 보습", "desc": "손과 얼굴에 수분을 보충해 피부 회복을 돕습니다.", "component": "피부"},
            {"title": "서 있기 10분", "desc": "앉지 않고 서 있는 것만으로도 혈액 순환이 개선됩니다.", "component": "순환"},
        ],
    },
    "medium": {
        "label": "3~6시간 대기",
        "items": [
            {"title": "라운지/좌석에서 20분 눈 붙이기", "desc": "짧은 낮잠으로 수면 부채를 일부 줄일 수 있습니다.", "component": "수면"},
            {"title": "가벼운 스트레칭 10분", "desc": "장시간 앉아있던 근육의 순환을 돕습니다.", "component": "순환"},
            {"title": "따뜻한 물/차 마시기", "desc": "카페인 없는 수분 섭취로 탈수를 예방합니다.", "component": "수분"},
        ],
    },
    "long": {
        "label": "6시간 이상 대기",
        "items": [
            {"title": "환승 호텔/라운지에서 휴식", "desc": "가능하면 충분히 눕거나 휴식할 공간을 찾으세요.", "component": "수면"},
            {"title": "가벼운 식사", "desc": "혈당을 안정시켜 컨디션 저하를 예방합니다.", "component": "순환"},
            {"title": "샤워/세안", "desc": "장시간 이동으로 지친 피부를 정돈합니다.", "component": "피부"},
        ],
    },
}


def get_layover_guide(max_layover_minutes):
    if not max_layover_minutes:
        return None
    hours = max_layover_minutes / 60
    if hours < 1:
        return None
    if hours <= 3:
        return LAYOVER_GUIDE_CATALOG["short"]
    if hours <= 6:
        return LAYOVER_GUIDE_CATALOG["medium"]
    return LAYOVER_GUIDE_CATALOG["long"]