def clamp_score(value):
    return max(0, min(100, round(value)))


def calculate_target_score(actual_score, remaining_minutes):
    if actual_score is None:
        return None
    capped_minutes = min(remaining_minutes, 3 * 24 * 60)
    recoverable = max(0, capped_minutes // 240) * 6
    return clamp_score(actual_score + recoverable)

SLEEP_PENALTY_PER_TZ_HOUR = 2
CIRCULATION_BASE_PENALTY = 1
CIRCULATION_PENALTY_PER_FLIGHT_HOUR = 1
HYDRATION_BASE_PENALTY = 1
HYDRATION_PENALTY_PER_FLIGHT_HOUR = 1
SKIN_PENALTY_PER_FLIGHT_HOUR = 0.9

LAYOVER_CIRCULATION_PENALTY = {
    "none": 0,
    "one": 2,
    "two_plus": 4,
}


def calculate_expected_score(total_flight_minutes, timezone_diff_minutes, layover_count):
    flight_hours = total_flight_minutes / 60
    tz_hours = abs(timezone_diff_minutes or 0) / 60

    sleep_penalty = tz_hours * SLEEP_PENALTY_PER_TZ_HOUR
    circulation_penalty = (
        flight_hours * CIRCULATION_PENALTY_PER_FLIGHT_HOUR
        + CIRCULATION_BASE_PENALTY
        + LAYOVER_CIRCULATION_PENALTY.get(layover_count, 0)
    )
    hydration_penalty = (
        flight_hours * HYDRATION_PENALTY_PER_FLIGHT_HOUR + HYDRATION_BASE_PENALTY
    )
    skin_penalty = flight_hours * SKIN_PENALTY_PER_FLIGHT_HOUR

    breakdown = {
        "sleep": -round(sleep_penalty),
        "circulation": -round(circulation_penalty),
        "hydration": -round(hydration_penalty),
        "skin": -round(skin_penalty),
    }
    total_penalty = -sum(breakdown.values())
    score = clamp_score(100 - total_penalty)
    return score, breakdown

CHECK_TYPE_TO_COMPONENT = {
    "water": "hydration",
    "stretch": "circulation",
    "moisturize": "skin",
    "sleep": "sleep",
}
OFFSET_PER_CHECK_COUNT = 1


def calculate_actual_score(expected_score, score_breakdown, inflight_checks):
    """
    inflight_checks: InflightCheck 쿼리셋 또는 리스트
    기내 기록이 없으면 예상 점수를 그대로 실측 점수로 사용한다.
    """
    checks = list(inflight_checks)
    if not checks:
        return expected_score, score_breakdown

    offsets = {"sleep": 0, "circulation": 0, "hydration": 0, "skin": 0}
    for check in checks:
        component = CHECK_TYPE_TO_COMPONENT.get(check.check_type)
        if component:
            offsets[component] += check.count * OFFSET_PER_CHECK_COUNT

    new_breakdown = {}
    for component, penalty in score_breakdown.items():
        # penalty는 0 이하 값(예: -14). 상쇄량이 감점 크기를 넘지 않도록 상한을 둠
        capped_offset = min(offsets.get(component, 0), abs(penalty))
        new_breakdown[component] = penalty + capped_offset

    total_penalty = -sum(new_breakdown.values())
    actual_score = clamp_score(100 - total_penalty)
    return actual_score, new_breakdown