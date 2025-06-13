from django.urls import path
from .views import SummarizeView, SummaryListView, SummaryDetailView, PDFUploadView

urlpatterns = [
    path('summarize/', SummarizeView.as_view(), name="summarize"),
    path('summaries/', SummaryListView.as_view(), name="summary-list"),
    path('summaries/<int:pk>/', SummaryDetailView.as_view(), name="summary-detail"),
    path('upload/', PDFUploadView.as_view(), name="pdf-upload"),
]
