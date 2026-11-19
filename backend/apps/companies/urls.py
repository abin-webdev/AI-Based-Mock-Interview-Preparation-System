from django.urls import path
from .views import (
    CompanyDashboardView,
    CompanyProfileView,
    CompanyVacancyListCreateView,
    CompanyVacancyDetailView,
    CompanyVacancyApplicationsListView,
    CompanyAllApplicationsListView,
    CompanyApplicationDetailView,
    CompanyApplicationStatusUpdateView,
    CompanyReviewsListView,
)

app_name = 'companies'

urlpatterns = [
    # Dashboard
    path('dashboard/', CompanyDashboardView.as_view(), name='dashboard'),

    # Profile
    path('profile/', CompanyProfileView.as_view(), name='profile'),

    # Vacancy Management
    path('vacancies/', CompanyVacancyListCreateView.as_view(), name='vacancy_list_create'),
    path('vacancies/<int:pk>/', CompanyVacancyDetailView.as_view(), name='vacancy_detail'),
    path('vacancies/<int:vacancy_id>/applications/', CompanyVacancyApplicationsListView.as_view(), name='vacancy_applications'),

    # Application Management
    path('applications/', CompanyAllApplicationsListView.as_view(), name='all_applications'),
    path('applications/<int:pk>/', CompanyApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/status/', CompanyApplicationStatusUpdateView.as_view(), name='application_status_update'),

    # Reviews
    path('reviews/', CompanyReviewsListView.as_view(), name='reviews'),
]
