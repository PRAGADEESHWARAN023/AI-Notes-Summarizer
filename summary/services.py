"""Business logic for turning an uploaded PDF into a saved Summary.

Views should only handle HTTP; everything about *what* happens to a PDF
lives here so it can be tested without making a request.
"""
import logging

import pymupdf

from .llm import summarize_text
from .models import Summary

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


class SummarizationError(Exception):
    """A problem with the user's file. The message is safe to show them."""


def validate_pdf(uploaded_file) -> None:
    if not uploaded_file.name.lower().endswith(".pdf"):
        raise SummarizationError("Please upload a PDF file.")

    if uploaded_file.size > MAX_PDF_BYTES:
        raise SummarizationError("PDF is too large (maximum 10 MB).")

    # Real PDFs start with %PDF-, whatever the file extension says.
    header = uploaded_file.read(5)
    uploaded_file.seek(0)
    if header != b"%PDF-":
        raise SummarizationError("This file is not a valid PDF.")


def extract_text(uploaded_file) -> str:
    uploaded_file.seek(0)
    try:
        with pymupdf.open(stream=uploaded_file.read(), filetype="pdf") as pdf:
            text = "\n".join(page.get_text() for page in pdf)
    except (RuntimeError, ValueError) as exc:
        logger.warning("Could not open PDF %s: %s", uploaded_file.name, exc)
        raise SummarizationError("This PDF could not be read.") from exc

    if not text.strip():
        raise SummarizationError(
            "No readable text found. Scanned PDFs are not supported yet."
        )
    return text


def summarize_pdf(user, uploaded_file) -> Summary:
    """Validate, extract, summarize and save. Returns the new Summary."""
    validate_pdf(uploaded_file)
    text = extract_text(uploaded_file)
    summary_text = summarize_text(text)  # may raise LLMError

    uploaded_file.seek(0)  # extraction consumed the file; rewind to save it
    return Summary.objects.create(
        user=user,
        filename=uploaded_file.name,
        summary=summary_text,
        pdf_file=uploaded_file,
    )