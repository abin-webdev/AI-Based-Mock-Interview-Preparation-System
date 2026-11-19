from django.urls import path
from .views import (
    PublicVacancyListView,
    PublicVacancyDetailView,
    VacancyApplyView,
)

app_name = 'vacancies'

urlpatterns = [
    path('', PublicVacancyListView.as_view(), name='vacancy_list'),
    path('<int:pk>/', PublicVacancyDetailView.as_view(), name='vacancy_detail'),
    path('<int:pk>/apply/', VacancyApplyView.as_view(), name='vacancy_apply'),
]
