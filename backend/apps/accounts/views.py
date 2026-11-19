from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User
from .serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    CandidateRegistrationSerializer,
    CompanyRegistrationSerializer,
    ChangePasswordSerializer,
)


@extend_schema(tags=['Authentication'])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Authenticate user via email or username and return JWT access and refresh tokens
    along with user metadata and role.
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Authentication'])
class CandidateRegistrationView(generics.CreateAPIView):
    """
    Register a new Candidate account and candidate profile.
    """
    queryset = User.objects.all()
    serializer_class = CandidateRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'ok',
            'message': 'Candidate registered successfully.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Authentication'])
class CompanyRegistrationView(generics.CreateAPIView):
    """
    Register a new Company account. Verification status defaults to PENDING.
    """
    queryset = User.objects.all()
    serializer_class = CompanyRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'ok',
            'message': 'Company registered successfully. Account is pending admin verification.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Authentication'])
class CurrentUserView(APIView):
    """
    Get profile, role, and permission details of the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data
        if user.role == User.Role.COMPANY:
            profile = getattr(user, 'company_profile', None)
            if profile:
                data['company_details'] = {
                    'company_name': profile.company_name,
                    'phone': profile.phone,
                    'address': profile.address,
                    'website': profile.website,
                    'verification_status': profile.verification_status,
                    'is_verified': profile.is_verified,
                    'logo': profile.logo.url if profile.logo else None,
                }
        elif user.role == User.Role.CANDIDATE:
            profile = getattr(user, 'candidate_profile', None)
            if profile:
                data['candidate_details'] = {
                    'full_name': profile.full_name,
                    'phone': profile.phone,
                    'dob': profile.dob,
                    'gender': profile.gender,
                    'place': profile.place,
                    'city': profile.city,
                    'state': profile.state,
                    'post': profile.post,
                    'pin': profile.pin,
                    'photo': profile.photo.url if profile.photo else None,
                    'resume': profile.resume.url if profile.resume else None,
                }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Authentication'])
class ChangePasswordView(APIView):
    """
    Change user password with old password verification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'ok', 'message': 'Password updated successfully.'})


@extend_schema(tags=['Authentication'])
class LogoutView(APIView):
    """
    Logout user by blacklisting the provided refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'ok', 'message': 'Logged out successfully.'})
        except Exception:
            return Response({'error': 'Invalid token or token already blacklisted.'}, status=status.HTTP_400_BAD_REQUEST)
