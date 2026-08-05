def clamp_score(value):
    return max(0, min(100, round(value)))


def calculate_target_score(actual_score, remaining_minutes):
    if actual_score is None:
        return None
    recoverable = max(0, remaining_minutes // 240) * 6
    return clamp_score(actual_score + recoverable)
