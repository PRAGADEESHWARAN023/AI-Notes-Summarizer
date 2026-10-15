from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from summary.llm import LLMError
from summary.models import Summary

from .conftest import pdf_upload


def post_file(client, upload):
    return client.post(reverse("summarize"), {"file": upload}, format="multipart")


def test_summarize_requires_login():
    response = post_file(APIClient(), pdf_upload())
    assert response.status_code == 401


def test_history_requires_login():
    response = APIClient().get(reverse("summary-list"))
    assert response.status_code == 401


def test_summarize_success(auth_client, mock_llm):
    response = post_file(auth_client, pdf_upload("notes.pdf"))

    assert response.status_code == 200
    assert response.json()["summary"] == "MOCK SUMMARY"
    assert Summary.objects.count() == 1


def test_summarize_without_file_is_400(auth_client):
    response = auth_client.post(reverse("summarize"), {}, format="multipart")
    assert response.status_code == 400


def test_summarize_invalid_file_is_400(auth_client, mock_llm):
    upload = SimpleUploadedFile("evil.pdf", b"not a pdf")
    response = post_file(auth_client, upload)

    assert response.status_code == 400
    assert "not a valid PDF" in response.json()["detail"]
    assert Summary.objects.count() == 0


def test_llm_outage_returns_502_and_saves_nothing(auth_client, monkeypatch):
    def broken_llm(text):
        raise LLMError("provider down")

    monkeypatch.setattr("summary.services.summarize_text", broken_llm)
    response = post_file(auth_client, pdf_upload())

    assert response.status_code == 502
    assert Summary.objects.count() == 0


def test_history_only_shows_own_summaries(auth_client, user, other_user):
    Summary.objects.create(user=user, filename="mine.pdf", summary="a", pdf_file="pdfs/mine.pdf")
    Summary.objects.create(user=other_user, filename="theirs.pdf", summary="b", pdf_file="pdfs/theirs.pdf")

    response = auth_client.get(reverse("summary-list"))

    assert response.status_code == 200
    names = [item["filename"] for item in response.json()]
    assert names == ["mine.pdf"]


def test_cannot_open_another_users_summary(auth_client, other_user):
    theirs = Summary.objects.create(
        user=other_user, filename="theirs.pdf", summary="b", pdf_file="pdfs/theirs.pdf"
    )

    response = auth_client.get(reverse("summary-detail", args=[theirs.id]))

    assert response.status_code == 404