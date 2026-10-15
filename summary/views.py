from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from .models import Summary
from .serializers import SummarySerializer
from .llm import summarize_text
import pymupdf

doc = pymupdf.open(...)
class SummaryListView(generics.ListAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class SummaryDetailView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user)


class BasePDFSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def extract_text_from_pdf(self, uploaded_file):
        with fitz.open(
            stream=uploaded_file.read(),
            filetype="pdf",
        ) as pdf:
            return "\n".join(page.get_text() for page in pdf)

    def get_summary(self, text):
        if not text.strip():
            raise ValueError(
                "No readable text found in the PDF."
            )

        return summarize_text(text)

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if (
            not uploaded_file
            or not uploaded_file.name.lower().endswith(".pdf")
        ):
            return Response(
                {"detail": "Please upload a valid PDF file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            full_text = self.extract_text_from_pdf(uploaded_file)
            summary_text = self.get_summary(full_text)

            return self.build_response(
                request,
                uploaded_file,
                summary_text,
            )

        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "PDF summarization failed"
            )

            return Response(
                {
                    "detail": (
                        "Error during summarization. "
                        "Please check the server logs."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def build_response(self, request, uploaded_file, summary_text):
        raise NotImplementedError


class SummarizeView(BasePDFSummaryView):
    def build_response(self, request, uploaded_file, summary_text):
        Summary.objects.create(
            user=request.user,
            filename=uploaded_file.name,
            summary=summary_text,
            pdf_file=uploaded_file,
        )

        return Response(
            {"summary": summary_text},
            status=status.HTTP_200_OK,
        )


class PDFUploadView(BasePDFSummaryView):
    def build_response(self, request, uploaded_file, summary_text):
        return Response(
            {"summary": summary_text},
            status=status.HTTP_200_OK,
        )
