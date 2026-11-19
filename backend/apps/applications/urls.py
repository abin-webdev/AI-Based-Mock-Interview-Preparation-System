from django.urls import path
from .views import (
    MyApplicationsListView,
    ApplicationDetailView,
    ApplicationWithdrawView,
)

app_name = 'applications'

urlpatterns = [
    path('', MyApplicationsListView.as_view(), name='my_applications'),
    path('<int:pk>/', ApplicationDetailView.as_view(), name='application_detail'),
    path('<int:pk>/withdraw/', ApplicationWithdrawView.as_view(), name='application_withdraw'),
]
