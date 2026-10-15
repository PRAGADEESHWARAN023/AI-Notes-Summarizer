import pymupdf
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


def make_pdf(text="Photosynthesis converts light into chemical energy."):
    """Build a tiny real PDF in memory. Empty text gives a blank page."""
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def pdf_upload(name="notes.pdf", text="Photosynthesis converts light into chemical energy."):
    return SimpleUploadedFile(name, make_pdf(text), content_type="application/pdf")


@pytest.fixture(autouse=True)
def temp_media(settings, tmp_path):
    """Uploaded PDFs go to a throwaway folder, never your real media/."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def user(db):
    return User.objects.create_user("alice", password="pass12345")


@pytest.fixture
def other_user(db):
    return User.objects.create_user("bob", password="pass12345")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def mock_llm(monkeypatch):
    """Replace the AI call so tests are fast, free and deterministic."""
    monkeypatch.setattr("summary.services.summarize_text", lambda text: "MOCK SUMMARY")