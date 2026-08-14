from django.conf import settings
from openai import OpenAI, APIError, APITimeoutError
import re

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.AI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _client


def generate_text(system_prompt, user_prompt, max_tokens=800):
    if not settings.AI_API_KEY:
        return {"success": False, "text": ""}

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gemini-3.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            extra_body={"reasoning_effort": "low"},
        )
        text = response.choices[0].message.content.strip()
        text = _strip_markdown(text)
        if not text:
            return {"success": False, "text": ""}
        return {"success": True, "text": text}
    except (APIError, APITimeoutError, Exception):
        return {"success": False, "text": ""}

def _strip_markdown(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"[\(（][^)）]*[A-Za-z][^)）]*[\)）]", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"['‘’]", "", text)
    return text.strip()