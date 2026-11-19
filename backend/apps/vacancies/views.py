from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCandidateRole
from apps.candidates.models import CandidateProfile
from apps.applications.models import Application
from .models import Vacancy
from .serializers import (
    VacancyListSerializer,
    VacancyDetailSerializer,
    VacancyApplySerializer,
)


@extend_schema(tags=['Job Vacancies'])
class PublicVacancyListView(generics.ListAPIView):
    """
    Search, filter, and browse all currently active job vacancies.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VacancyListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'experience_years', 'company__id']
    search_fields = ['position', 'description', 'required_skills', 'company__company_name', 'location']
    ordering_fields = ['created_at', 'application_deadline', 'no_of_vacancy']
    ordering = ['-created_at']

    def get_queryset(self):
        # Auto-filter out closed vacancies and ensure company is approved
        today = timezone.localdate()
        return Vacancy.objects.filter(
            status='ACTIVE',
            application_deadline__gte=today,
            company__verification_status='APPROVED'
        ).select_related('company')


@extend_schema(tags=['Job Vacancies'])
class PublicVacancyDetailView(generics.RetrieveAPIView):
    """
    Retrieve full details of a specific job vacancy including company information.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VacancyDetailSerializer
    queryset = Vacancy.objects.filter(company__verification_status='APPROVED').select_related('company')


@extend_schema(tags=['Job Vacancies'])
class VacancyApplyView(APIView):
    """
    Apply for a job vacancy. Attaches uploaded resume or candidate's profile resume.
    Prevents duplicate applications.
    """
    permission_classes = [IsCandidateRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        try:
            vacancy = Vacancy.objects.get(pk=pk, company__verification_status='APPROVED')
        except Vacancy.DoesNotExist:
            return Response({'error': 'Vacancy not found or company not verified.'}, status=status.HTTP_404_NOT_FOUND)

        if vacancy.status != Vacancy.Status.ACTIVE or vacancy.is_expired:
            return Response({
                'error': 'This job vacancy is no longer accepting applications.'
            }, status=status.HTTP_400_BAD_REQUEST)

        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Duplicate check
        if Application.objects.filter(vacancy=vacancy, candidate=candidate).exists():
            return Response({
                'error': 'You have already applied for this job vacancy.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = VacancyApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_file = request.FILES.get('resume') or candidate.resume
        cover_letter = serializer.validated_data.get('cover_letter', '')

        application = Application.objects.create(
            vacancy=vacancy,
            candidate=candidate,
            resume=resume_file,
            cover_letter=cover_letter,
            status=Application.Status.PENDING
        )

        return Response({
            'status': 'ok',
            'message': 'Application submitted successfully.',
            'application_id': application.id,
            'vacancy': vacancy.position,
            'company': vacancy.company.company_name
        }, status=status.HTTP_201_CREATED)
