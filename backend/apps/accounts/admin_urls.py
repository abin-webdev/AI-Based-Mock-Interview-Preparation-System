from django.urls import path
from .admin_views import (
    AdminDashboardStatsView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserToggleActiveView,
    AdminCompanyListView,
    AdminCompanyDetailView,
    AdminCompanyVerifyView,
    AdminVacancyListView,
    AdminComplaintListView,
    AdminComplaintReplyView,
    AdminFeedbackListView,
    AdminInterviewMonitorView,
)

app_name = 'admin_api'

urlpatterns = [
    # Dashboard
    path('dashboard-stats/', AdminDashboardStatsView.as_view(), name='dashboard_stats'),

    # User Management
    path('users/', AdminUserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/toggle-active/', AdminUserToggleActiveView.as_view(), name='user_toggle_active'),

    # Company Management & Verification
    path('companies/', AdminCompanyListView.as_view(), name='company_list'),
    path('companies/<int:pk>/', AdminCompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/verify/', AdminCompanyVerifyView.as_view(), name='company_verify'),

    # Vacancy Audit
    path('vacancies/', AdminVacancyListView.as_view(), name='vacancy_list'),

    # Complaints Moderation
    path('complaints/', AdminComplaintListView.as_view(), name='complaint_list'),
    path('complaints/<int:pk>/reply/', AdminComplaintReplyView.as_view(), name='complaint_reply'),

    # Feedback Moderation
    path('feedback/', AdminFeedbackListView.as_view(), name='feedback_list'),

    # Interview Activity Monitoring
    path('interview-monitor/', AdminInterviewMonitorView.as_view(), name='interview_monitor'),
]
