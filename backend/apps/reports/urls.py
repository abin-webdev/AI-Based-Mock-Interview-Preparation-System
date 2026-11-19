from django.urls import path
from .views import AIMockInterviewPDFReportView

app_name = 'reports'

urlpatterns = [
    path('mock-interviews/<int:pk>/pdf/', AIMockInterviewPDFReportView.as_view(), name='mock_interview_pdf'),
]
