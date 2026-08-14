from . import prompts
from .client import generate_text
from .fallbacks import FALLBACK_MESSAGES


def get_expected_score_summary(trip):
    result = generate_text(prompts.SYSTEM_PROMPT, prompts.expected_score_summary_prompt(trip))
    return result["text"] if result["success"] else FALLBACK_MESSAGES["expected_score_summary"]


def get_score_diff_explanation(trip):
    result = generate_text(prompts.SYSTEM_PROMPT, prompts.score_diff_explanation_prompt(trip))
    return result["text"] if result["success"] else FALLBACK_MESSAGES["score_diff_explanation"]


def get_report_strength_weakness(trip, result_obj):
    result = generate_text(
        prompts.SYSTEM_PROMPT, prompts.report_strength_weakness_prompt(trip, result_obj)
    )
    return result["text"] if result["success"] else FALLBACK_MESSAGES["report_strength_weakness"]


def get_next_trip_improvement(trip, result_obj):
    result = generate_text(
        prompts.SYSTEM_PROMPT, prompts.next_trip_improvement_prompt(trip, result_obj)
    )
    return result["text"] if result["success"] else FALLBACK_MESSAGES["next_trip_improvement"]