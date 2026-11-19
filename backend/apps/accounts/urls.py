from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    CandidateRegistrationView,
    CompanyRegistrationView,
    CurrentUserView,
    ChangePasswordView,
    LogoutView,
)

app_name = 'accounts'

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/candidate/', CandidateRegistrationView.as_view(), name='register_candidate'),
    path('register/company/', CompanyRegistrationView.as_view(), name='register_company'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
