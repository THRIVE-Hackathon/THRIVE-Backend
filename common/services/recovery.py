from django.utils import timezone

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
    return [
        {"title": "터미널 산책", "desc": "순환을 돕고, 장시간 착석으로 굳은 다리를 풀어줘요.", "component": "순환"},
        {"title": "물 섭취", "desc": "기내 건조한 환경으로 손실된 수분을 보충하세요.", "component": "수분"},
        {"title": "세면대 보습", "desc": "얼굴과 손에 수분을 공급해 피부 장벽을 지켜요.", "component": "피부"},
        {"title": "10분 이상 서 있기", "desc": "서 있는 것만으로도 혈액 순환에 도움이 돼요.", "component": "순환"},
    ]


def get_or_create_recovery_items(trip):
    from recovery.models import RecoveryItem

    if trip.recovery_items.exists():
        return list(trip.recovery_items.all())

    now = timezone.now()

    items = [
        RecoveryItem(
            trip=trip,
            key=key,
            title=entry["title"],
            component=entry["component"],
            score_delta=entry["score_delta"],
            local_date=timezone.localdate(),
            scheduled_at=now,
        )
        for key, entry in RECOVERY_ITEM_CATALOG.items()
    ]
    RecoveryItem.objects.bulk_create(items)
    return list(trip.recovery_items.all())