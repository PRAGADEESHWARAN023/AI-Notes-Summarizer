import logging

from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

CHUNK_CHARS = 10000  # about 2,500 tokens: safe for free-tier token limits
MAX_CHUNKS = 8       # about 80,000 characters; longer PDFs are cut off

CHUNK_PROMPT = (
    "Summarize this section of study notes as 5-8 concise bullet points. "
    "Keep key terms, definitions, numbers and names. Do not invent facts."
)

FINAL_PROMPT = (
    "You summarize study notes. Reply in exactly this format:\n"
    "Title: one short line\n"
    "Summary: 3-4 sentences\n"
    "Key points:\n- 5 to 8 bullet points\n"
    "Terms to remember:\n- up to 5 items written as term: definition\n"
    "Use only facts from the text. Do not invent anything."
)


class LLMError(Exception):
    """The AI provider failed (bad key, rate limit, timeout, outage...)."""


def chunk_text(text: str, size: int | None = None) -> list[str]:
    """Split text into pieces of at most `size` characters, on line breaks."""
    size = size or CHUNK_CHARS
    chunks, current = [], ""
    for para in text.split("\n"):
        while len(para) > size:  # one giant line: hard split
            if current:
                chunks.append(current)
                current = ""
            chunks.append(para[:size])
            para = para[size:]
        if current and len(current) + len(para) + 1 > size:
            chunks.append(current)
            current = ""
        current += para + "\n"
    if current.strip():
        chunks.append(current)
    return [c for c in chunks if c.strip()]


def _ask(system: str, user: str) -> str:
    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        timeout=60,
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def summarize_text(text: str) -> str:
    chunks = chunk_text(text)
    if len(chunks) > MAX_CHUNKS:
        logger.warning("PDF has %d chunks; only the first %d are summarized",
                       len(chunks), MAX_CHUNKS)
        chunks = chunks[:MAX_CHUNKS]

    try:
        if len(chunks) == 1:
            return _ask(FINAL_PROMPT, chunks[0])

        # Long document: summarize each section, then merge the results.
        partials = [_ask(CHUNK_PROMPT, chunk) for chunk in chunks]
        merged = "\n\n".join(
            f"Section {i}:\n{partial}" for i, partial in enumerate(partials, 1)
        )
        return _ask(FINAL_PROMPT, merged)
    except OpenAIError as exc:
        logger.exception("LLM request failed")
        raise LLMError("LLM request failed") from exc