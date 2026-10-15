import pytest
from openai import OpenAIError

from summary import llm


def test_chunk_text_respects_size():
    text = "\n".join(["word " * 20] * 50)  # 50 lines of 100 characters
    chunks = llm.chunk_text(text, size=500)

    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)


def test_giant_line_is_split():
    chunks = llm.chunk_text("x" * 2500, size=1000)

    assert len(chunks) == 3
    assert all(len(c) <= 1001 for c in chunks)


def test_short_text_uses_a_single_call(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "_ask", lambda system, user: calls.append(system) or "done")

    assert llm.summarize_text("short notes") == "done"
    assert calls == [llm.FINAL_PROMPT]


def test_long_text_summarizes_sections_then_merges(monkeypatch):
    calls = []

    def fake_ask(system, user):
        calls.append(system)
        return "partial"

    monkeypatch.setattr(llm, "_ask", fake_ask)
    monkeypatch.setattr(llm, "CHUNK_CHARS", 100)

    llm.summarize_text("\n".join(["a" * 60] * 4))  # becomes 4 chunks

    assert calls.count(llm.CHUNK_PROMPT) == 4
    assert calls[-1] == llm.FINAL_PROMPT


def test_chunk_count_is_capped(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "_ask", lambda system, user: calls.append(system) or "p")
    monkeypatch.setattr(llm, "CHUNK_CHARS", 100)
    monkeypatch.setattr(llm, "MAX_CHUNKS", 3)

    llm.summarize_text("\n".join(["a" * 60] * 10))

    assert calls.count(llm.CHUNK_PROMPT) == 3


def test_provider_error_becomes_llm_error(monkeypatch):
    def boom(system, user):
        raise OpenAIError("provider down")

    monkeypatch.setattr(llm, "_ask", boom)

    with pytest.raises(llm.LLMError):
        llm.summarize_text("some notes")