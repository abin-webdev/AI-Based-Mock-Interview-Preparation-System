from django.urls import path
from .views import (
    CompanyTestListCreateView,
    CompanyTestDetailView,
    AssignCandidatesToTestView,
    RecordCandidateAttendanceView,
    CandidateMyTestsListView,
)

app_name = 'tests_app'

urlpatterns = [
    path('', CompanyTestListCreateView.as_view(), name='test_list_create'),
    path('my-tests/', CandidateMyTestsListView.as_view(), name='my_tests'),
    path('<int:pk>/', CompanyTestDetailView.as_view(), name='test_detail'),
    path('<int:pk>/assign-candidates/', AssignCandidatesToTestView.as_view(), name='assign_candidates'),
    path('<int:pk>/attendance/', RecordCandidateAttendanceView.as_view(), name='record_attendance'),
]
