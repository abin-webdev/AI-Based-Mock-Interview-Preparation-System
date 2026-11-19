from django.urls import path
from .views import (
    CandidateDashboardView,
    CandidateProfileView,
    CandidatePhotoUploadView,
    CandidateResumeUploadView,
)

app_name = 'candidates'

urlpatterns = [
    path('dashboard/', CandidateDashboardView.as_view(), name='dashboard'),
    path('profile/', CandidateProfileView.as_view(), name='profile'),
    path('profile/photo/', CandidatePhotoUploadView.as_view(), name='photo_upload'),
    path('profile/resume/', CandidateResumeUploadView.as_view(), name='resume_upload'),
]
