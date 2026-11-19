from django.urls import path
from .views import (
    CompanyInterviewListCreateView,
    CompanyInterviewDetailView,
    CompanyInterviewRescheduleView,
    CompanyInterviewCancelView,
    CandidateMyInterviewsListView,
    CandidateInterviewDetailView,
)

app_name = 'interviews'

urlpatterns = [
    path('', CompanyInterviewListCreateView.as_view(), name='interview_list_create'),
    path('my-interviews/', CandidateMyInterviewsListView.as_view(), name='my_interviews'),
    path('my-interviews/<int:pk>/', CandidateInterviewDetailView.as_view(), name='my_interview_detail'),
    path('<int:pk>/', CompanyInterviewDetailView.as_view(), name='interview_detail'),
    path('<int:pk>/reschedule/', CompanyInterviewRescheduleView.as_view(), name='reschedule_interview'),
    path('<int:pk>/cancel/', CompanyInterviewCancelView.as_view(), name='cancel_interview'),
]
