import logging

from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

MAX_CHARS = 12000  # free tiers limit tokens per minute

SYSTEM_PROMPT = (
    "You summarize study notes. Return a short summary, then "
    "5-8 key points as bullet points. Do not invent facts."
)


class LLMError(Exception):
    """The AI provider failed (bad key, rate limit, timeout, outage...)."""


def summarize_text(text: str) -> str:
    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        timeout=60,
    )
    try:
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text[:MAX_CHARS]},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as exc:
        logger.exception("LLM request failed")
        raise LLMError("LLM request failed") from exc