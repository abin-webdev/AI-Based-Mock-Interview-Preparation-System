from django.urls import path
from .views import ComplaintListCreateView, ComplaintDetailView

app_name = 'complaints'

urlpatterns = [
    path('', ComplaintListCreateView.as_view(), name='complaint_list_create'),
    path('<int:pk>/', ComplaintDetailView.as_view(), name='complaint_detail'),
]
