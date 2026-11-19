from django.urls import path
from .views import (
    LegacyUserLoginView,
    LegacyUserRegistrationView,
    LegacyUserProfileView,
    LegacyUserProfileViewForEditView,
    LegacyUserEditProfileView,
    LegacyCompanyDropdownView,
    LegacyReviewCompanyView,
    LegacyUserViewVacancyView,
    LegacyUserApplyVacancyView,
    LegacyViewAppliedVacancyView,
    LegacyUserViewTestView,
    LegacySendFeedbackView,
    LegacySendComplaintView,
    LegacyUserViewReplyView,
)

app_name = 'compatibility'

urlpatterns = [
    # Auth
    path('User_login/', LegacyUserLoginView.as_view(), name='legacy_user_login'),

    # Candidate Profile & Registration
    path('user_registration/', LegacyUserRegistrationView.as_view(), name='legacy_user_registration'),
    path('user_profile/', LegacyUserProfileView.as_view(), name='legacy_user_profile'),
    path('user_profileviewforedit/', LegacyUserProfileViewForEditView.as_view(), name='legacy_user_profileviewforedit'),
    path('user_edit_profile/', LegacyUserEditProfileView.as_view(), name='legacy_user_edit_profile'),

    # Vacancies & Applications
    path('user_view_vacancy/', LegacyUserViewVacancyView.as_view(), name='legacy_user_view_vacancy'),
    path('user_apply_vacancy/', LegacyUserApplyVacancyView.as_view(), name='legacy_user_apply_vacancy'),
    path('view_applied_vacancy/', LegacyViewAppliedVacancyView.as_view(), name='legacy_view_applied_vacancy'),

    # Company dropdown & reviews
    path('companytocomplaint/', LegacyCompanyDropdownView.as_view(), name='legacy_company_dropdown'),
    path('review_company/', LegacyReviewCompanyView.as_view(), name='legacy_review_company'),

    # Tests & Assessments
    path('user_view_test/', LegacyUserViewTestView.as_view(), name='legacy_user_view_test'),

    # Feedback & Complaints
    path('send_feedback/', LegacySendFeedbackView.as_view(), name='legacy_send_feedback'),
    path('send_complaint/', LegacySendComplaintView.as_view(), name='legacy_send_complaint'),
    path('user_viewreply/', LegacyUserViewReplyView.as_view(), name='legacy_user_viewreply'),
]
