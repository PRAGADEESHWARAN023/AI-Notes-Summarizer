import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from summary.models import Summary
from summary.services import SummarizationError, summarize_pdf

from .conftest import pdf_upload


def fail_if_called(text):
    pytest.fail("The LLM must not be called for an invalid file")


def test_valid_pdf_is_summarized_and_saved(user, mock_llm):
    result = summarize_pdf(user, pdf_upload("biology.pdf"))

    assert result.summary == "MOCK SUMMARY"
    assert result.filename == "biology.pdf"
    assert result.user == user
    assert Summary.objects.count() == 1


def test_llm_receives_the_extracted_text(user, monkeypatch):
    received = {}

    def fake_llm(text):
        received["text"] = text
        return "ok"

    monkeypatch.setattr("summary.services.summarize_text", fake_llm)
    summarize_pdf(user, pdf_upload(text="Mitochondria make ATP."))

    assert "Mitochondria make ATP." in received["text"]


def test_rejects_wrong_extension(user, monkeypatch):
    monkeypatch.setattr("summary.services.summarize_text", fail_if_called)
    upload = SimpleUploadedFile("notes.txt", b"hello")

    with pytest.raises(SummarizationError, match="PDF"):
        summarize_pdf(user, upload)
    assert Summary.objects.count() == 0


def test_rejects_fake_pdf(user, monkeypatch):
    """Right extension, wrong contents."""
    monkeypatch.setattr("summary.services.summarize_text", fail_if_called)
    upload = SimpleUploadedFile("evil.pdf", b"this is not a pdf")

    with pytest.raises(SummarizationError, match="not a valid PDF"):
        summarize_pdf(user, upload)


def test_rejects_oversized_pdf(user, monkeypatch):
    monkeypatch.setattr("summary.services.MAX_PDF_BYTES", 10)
    monkeypatch.setattr("summary.services.summarize_text", fail_if_called)

    with pytest.raises(SummarizationError, match="too large"):
        summarize_pdf(user, pdf_upload())


def test_rejects_pdf_without_text(user, monkeypatch):
    monkeypatch.setattr("summary.services.summarize_text", fail_if_called)

    with pytest.raises(SummarizationError, match="No readable text"):
        summarize_pdf(user, pdf_upload(text=""))