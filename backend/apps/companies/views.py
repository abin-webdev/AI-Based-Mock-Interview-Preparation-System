from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCompanyRole, IsVerifiedCompany
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from .models import CompanyProfile, CompanyReview
from .serializers import (
    CompanyProfileSerializer,
    CompanyProfileUpdateSerializer,
    CompanyVacancySerializer,
    CompanyApplicationSerializer,
    CompanyApplicationStatusUpdateSerializer,
    CompanyReviewSerializer,
)


@extend_schema(tags=['Company Portal'])
class CompanyDashboardView(APIView):
    """
    Returns metrics and statistics for the company's portal dashboard.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        vacancies = Vacancy.objects.filter(company=company)
        total_vacancies = vacancies.count()
        active_vacancies = vacancies.filter(status='ACTIVE').count()

        applications = Application.objects.filter(vacancy__company=company)
        total_applications = applications.count()
        pending_applications = applications.filter(status='PENDING').count()
        shortlisted_applications = applications.filter(status='SHORTLISTED').count()
        accepted_applications = applications.filter(status='ACCEPTED').count()
        rejected_applications = applications.filter(status='REJECTED').count()

        reviews = CompanyReview.objects.filter(company=company)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0

        return Response({
            'company': {
                'id': company.id,
                'name': company.company_name,
                'verification_status': company.verification_status,
                'is_verified': company.is_verified,
            },
            'vacancies': {
                'total': total_vacancies,
                'active': active_vacancies,
            },
            'applications': {
                'total': total_applications,
                'pending': pending_applications,
                'shortlisted': shortlisted_applications,
                'accepted': accepted_applications,
                'rejected': rejected_applications,
            },
            'reviews': {
                'count': reviews.count(),
                'average_rating': round(float(avg_rating), 1),
            }
        })


@extend_schema(tags=['Company Portal'])
class CompanyProfileView(APIView):
    """
    Retrieve and update the authenticated company's profile.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanyProfileSerializer(company)
        return Response(serializer.data)

    def put(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanyProfileUpdateSerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'ok',
            'message': 'Company profile updated successfully.',
            'profile': CompanyProfileSerializer(company).data
        })


@extend_schema(tags=['Company Portal'])
class CompanyVacancyListCreateView(APIView):
    """
    List company's own vacancies or create a new vacancy.
    Only verified companies (APPROVED) can create vacancies.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        vacancies = Vacancy.objects.filter(company=company).order_by('-created_at')
        status_param = request.query_params.get('status')
        if status_param:
            vacancies = vacancies.filter(status=status_param.upper())
        serializer = CompanyVacancySerializer(vacancies, many=True)
        return Response(serializer.data)

    def post(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company:
            return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not company.is_verified:
            return Response({
                'status': 'error',
                'message': f"Your account status is '{company.verification_status}'. Only approved and verified companies can publish job vacancies."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyVacancySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vacancy = serializer.save(company=company)
        return Response({
            'status': 'ok',
            'message': 'Job vacancy posted successfully.',
            'vacancy': CompanyVacancySerializer(vacancy).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Company Portal'])
class CompanyVacancyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a company's job vacancy.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = CompanyVacancySerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        return Vacancy.objects.filter(company=company)


@extend_schema(tags=['Company Portal'])
class CompanyVacancyApplicationsListView(generics.ListAPIView):
    """
    List all candidate applications received for a specific vacancy.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = CompanyApplicationSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        vacancy_id = self.kwargs.get('vacancy_id')
        queryset = Application.objects.filter(
            vacancy__id=vacancy_id,
            vacancy__company=company
        ).select_related('candidate__user', 'vacancy').order_by('-applied_at')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset


@extend_schema(tags=['Company Portal'])
class CompanyAllApplicationsListView(generics.ListAPIView):
    """
    List all candidate applications received across all company vacancies.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = CompanyApplicationSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        queryset = Application.objects.filter(
            vacancy__company=company
        ).select_related('candidate__user', 'vacancy').order_by('-applied_at')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset


@extend_schema(tags=['Company Portal'])
class CompanyApplicationDetailView(generics.RetrieveAPIView):
    """
    View complete candidate details, resume, and application notes.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = CompanyApplicationSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        return Application.objects.filter(vacancy__company=company).select_related('candidate__user', 'vacancy')


@extend_schema(tags=['Company Portal'])
class CompanyApplicationStatusUpdateView(APIView):
    """
    Update application status: SHORTLISTED, REJECTED, ACCEPTED, PENDING.
    """
    permission_classes = [IsCompanyRole]

    def post(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            application = Application.objects.get(pk=pk, vacancy__company=company)
        except Application.DoesNotExist:
            return Response({'error': 'Application not found for your company.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompanyApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        company_notes = serializer.validated_data.get('company_notes', '')

        application.status = new_status
        if company_notes:
            application.company_notes = company_notes
        application.save()

        return Response({
            'status': 'ok',
            'message': f"Candidate application marked as {new_status}.",
            'application_id': application.id,
            'new_status': application.status,
            'company_notes': application.company_notes
        })


@extend_schema(tags=['Company Portal'])
class CompanyReviewsListView(generics.ListAPIView):
    """
    View reviews and star ratings received from candidates.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = CompanyReviewSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        return CompanyReview.objects.filter(company=company).select_related('candidate').order_by('-created_at')
