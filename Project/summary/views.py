from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from .models import Summary
from .serializers import SummarySerializer
import fitz  # PyMuPDF
import google.generativeai as genai
from django.conf import settings


class SummaryListView(generics.ListAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user).order_by('-created_at')


class SummaryDetailView(generics.RetrieveAPIView):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Summary.objects.filter(user=self.request.user)


class SummarizeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file or not uploaded_file.name.endswith('.pdf'):
            return Response({"detail": "Please upload a valid PDF file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            full_text = self.extract_text_from_pdf(uploaded_file)
            summary_text = self.get_summary(full_text)

            Summary.objects.create(
                user=request.user,
                filename=uploaded_file.name,
                summary=summary_text,
                pdf_file=uploaded_file
            )

            return Response({"summary": summary_text}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Error during summarization: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_text_from_pdf(self, uploaded_file):
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in pdf:
            full_text += page.get_text()
        pdf.close()
        return full_text

    def get_summary(self, text):
        genai.configure(api_key=settings.GENAI_API_KEY)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")  # or "gemini-pro"
        response = model.generate_content(text)
        return response.text.strip()


class PDFUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file or not uploaded_file.name.endswith('.pdf'):
            return Response({"detail": "Please upload a valid PDF file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            full_text = self.extract_text_from_pdf(uploaded_file)
            summary_text = self.get_summary(full_text)
            return Response({"summary": summary_text}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Error during summarization: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_text_from_pdf(self, uploaded_file):
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in pdf:
            full_text += page.get_text()
        pdf.close()
        return full_text

    def get_summary(self, text):
        genai.configure(api_key=settings.GENAI_API_KEY)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")  # or "gemini-pro"
        response = model.generate_content(text)
        return response.text.strip()
