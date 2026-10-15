from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .llm import LLMError
from .models import Summary
from .serializers import SummarySerializer
from .services import SummarizationError, summarize_pdf


class SummaryListView(generics.ListAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user).order_by("-created_at")


class SummaryDetailView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user)


class SummarizeView(APIView):
    """POST a PDF as multipart field "file"; returns its summary."""

    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response(
                {"detail": "Please upload a PDF file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            summary = summarize_pdf(request.user, uploaded_file)
        except SummarizationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except LLMError:
            return Response(
                {"detail": "The AI service is unavailable. Please try again shortly."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"id": summary.id, "summary": summary.summary},
            status=status.HTTP_200_OK,
        )