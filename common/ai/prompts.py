SYSTEM_PROMPT = (
    "당신은 장거리 비행 회복을 돕는 코치입니다. "
    "의학적 진단이나 처방으로 오해될 수 있는 표현은 절대 쓰지 않습니다. "
    "마크다운(별표, 굵은글씨 등) 없이 순수 텍스트로만 답합니다. "
    "영어 단어나 괄호 병기(예: '딥 슬립(Deep Sleep)') 없이 한국어로만 답합니다. "
    "숫자는 반드시 아라비아 숫자로만 표기합니다 (예: '26점', '이십육 점'처럼 한글로 풀어 쓰지 않습니다). "
    "'~것 같아요', '~해요'처럼 친근한 존댓말 어미를 사용하고, "
    "숫자(점수)는 문장 안에 자연스럽게 녹여서 말합니다. "
    "과장된 수식어(압도적인, 완벽히, 최악의 등) 없이 담백하게, 한두 문장으로 짧게 답합니다."
)

def expected_score_summary_prompt(trip):
    return (
        f"{trip.route_name} 여정, 총 비행시간 {trip.total_flight_minutes}분, "
        f"시차 {abs(trip.timezone_diff_minutes or 0)}분입니다. "
        f"요소별 예상 감점: {trip.score_breakdown}. "
        "이 중 가장 회복에 시간이 필요한 요소가 무엇인지 한 문장으로 짚어주세요. "
        "예시 톤: '시차와 장시간 비행으로 수면·리듬 회복이 가장 많은 시간이 필요할 것 같아요.'"
    )


def score_diff_explanation_prompt(trip):
    diff = (trip.actual_score or 0) - (trip.expected_score or 0)
    checks_summary = [
        f"{c.get_check_type_display()} {c.count}회" for c in trip.inflight_checks.all() if c.count > 0
    ]
    return (
        f"예상 점수 {trip.expected_score}점, 실측 점수 {trip.actual_score}점으로 "
        f"{diff:+d}점 차이가 났습니다. "
        f"기내 실천 기록: {', '.join(checks_summary) if checks_summary else '없음'}. "
        "이 차이가 난 이유를 기내 실천 기록과 연결해서 한 문장으로 설명해주세요. "
        "예시 톤: '기내에서 수분 보충과 보습을 꾸준히 실천한 덕분에 예상 점수보다 6점 높은 상태에요.'"
    )


def recovery_item_reason_prompt(item):
    return (
        f"'{item.title}' 항목은 {item.get_component_display()} 회복에 "
        f"+{item.score_delta}점 도움이 됩니다. "
        "이 항목이 왜 도움이 되는지 한 문장으로 설명해주세요."
    )


def report_strength_weakness_prompt(trip, result):
    return (
        f"여정 회복 결과: 착륙 시점 {trip.actual_score}점 → 최종 {trip.current_score}점. "
        f"요소별 회복 근거: {trip.score_breakdown}. "
        f"일정 차질도: {result.disruption_score}점(0=차질없음, 5=크게 차질). "
        "어떤 요소가 잘 회복됐고 어떤 요소가 더디었는지 한두 문장으로 분석해주세요."
    )


def next_trip_improvement_prompt(trip, result):
    return (
        f"이번 여정({trip.route_name})에서 회복이 가장 더뎠던 요소와 "
        f"일정 차질도 {result.disruption_score}점을 참고해서, "
        "다음 장거리 비행 때 실천하면 좋을 개선 제안을 한 문장으로 해주세요."
    )