from django.urls import path
from .views import (
    CandidateSessionListCreateView,
    CandidateSessionDetailView,
    CandidateSessionStartView,
    CandidateSessionQuestionsListView,
    CandidateSubmitAnswerView,
    CandidateAbandonSessionView,
    CandidateCompleteSessionView,
    CandidateUploadCameraTelemetryView,
    CandidateSessionResultsView,
    CompanyCandidateInterviewResultsView,
)

app_name = 'ai_interviews'

urlpatterns = [
    path('sessions/', CandidateSessionListCreateView.as_view(), name='session_list_create'),
    path('sessions/<int:pk>/', CandidateSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/start/', CandidateSessionStartView.as_view(), name='session_start'),
    path('sessions/<int:pk>/questions/', CandidateSessionQuestionsListView.as_view(), name='session_questions'),
    path('sessions/<int:pk>/submit-answer/', CandidateSubmitAnswerView.as_view(), name='session_submit_answer'),
    path('sessions/<int:pk>/abandon/', CandidateAbandonSessionView.as_view(), name='session_abandon'),
    path('sessions/<int:pk>/complete/', CandidateCompleteSessionView.as_view(), name='session_complete'),
    path('sessions/<int:pk>/camera-telemetry/', CandidateUploadCameraTelemetryView.as_view(), name='session_camera_telemetry'),
    path('sessions/<int:pk>/results/', CandidateSessionResultsView.as_view(), name='session_results'),
    path('sessions/<int:pk>/company-results/', CompanyCandidateInterviewResultsView.as_view(), name='session_company_results'),
]
