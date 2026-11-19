from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsAdminRole
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy
from apps.complaints.models import Complaint
from apps.feedback.models import Feedback
from apps.ai_interviews.models import AIMockSession

from .admin_serializers import (
    AdminUserListSerializer,
    AdminCompanyListSerializer,
    AdminCompanyDetailSerializer,
    AdminCompanyVerifySerializer,
    AdminComplaintSerializer,
    AdminComplaintReplySerializer,
    AdminFeedbackSerializer,
    AdminVacancyListSerializer,
    AdminInterviewMonitorSerializer,
)

User = get_user_model()


@extend_schema(tags=['Admin Module'])
class AdminDashboardStatsView(APIView):
    """
    Returns aggregated metrics and statistics for the Administrator Dashboard.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        total_users = User.objects.count()
        candidates_count = User.objects.filter(role=User.Role.CANDIDATE).count()
        companies_count = User.objects.filter(role=User.Role.COMPANY).count()
        admins_count = User.objects.filter(role=User.Role.ADMIN).count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()

        # Company verification breakdown
        companies_pending = CompanyProfile.objects.filter(verification_status='PENDING').count()
        companies_approved = CompanyProfile.objects.filter(verification_status='APPROVED').count()
        companies_rejected = CompanyProfile.objects.filter(verification_status='REJECTED').count()
        companies_suspended = CompanyProfile.objects.filter(verification_status='SUSPENDED').count()

        # Vacancies breakdown
        total_vacancies = Vacancy.objects.count()
        active_vacancies = Vacancy.objects.filter(status='ACTIVE').count()
        closed_vacancies = Vacancy.objects.filter(status='CLOSED').count()

        # Complaints breakdown
        total_complaints = Complaint.objects.count()
        pending_complaints = Complaint.objects.filter(status='PENDING').count()
        resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()

        # Feedback & AI interviews
        total_feedback = Feedback.objects.count()
        total_mock_sessions = AIMockSession.objects.count()
        completed_mock_sessions = AIMockSession.objects.filter(status='COMPLETED').count()

        return Response({
            'users': {
                'total': total_users,
                'candidates': candidates_count,
                'companies': companies_count,
                'admins': admins_count,
                'active': active_users,
                'inactive': inactive_users,
            },
            'companies': {
                'total': companies_count,
                'pending': companies_pending,
                'approved': companies_approved,
                'rejected': companies_rejected,
                'suspended': companies_suspended,
            },
            'vacancies': {
                'total': total_vacancies,
                'active': active_vacancies,
                'closed': closed_vacancies,
            },
            'complaints': {
                'total': total_complaints,
                'pending': pending_complaints,
                'resolved': resolved_complaints,
            },
            'feedback': {
                'total': total_feedback,
            },
            'ai_interviews': {
                'total_sessions': total_mock_sessions,
                'completed': completed_mock_sessions,
            }
        })


@extend_schema(tags=['Admin Module'])
class AdminUserListView(generics.ListAPIView):
    """
    List all registered users with optional role filtering and keyword search.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ('true', '1'))
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(email__icontains=search) | queryset.filter(username__icontains=search)
        return queryset


@extend_schema(tags=['Admin Module'])
class AdminUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve detailed information about a specific user account.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserListSerializer
    queryset = User.objects.all()


@extend_schema(tags=['Admin Module'])
class AdminUserToggleActiveView(APIView):
    """
    Activate or deactivate a user account.
    """
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user == request.user:
            return Response({'error': 'You cannot deactivate your own admin account.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = not user.is_active
        user.save()
        state = 'activated' if user.is_active else 'deactivated'
        return Response({
            'status': 'ok',
            'message': f"User account has been {state}.",
            'is_active': user.is_active
        })


@extend_schema(tags=['Admin Module'])
class AdminCompanyListView(generics.ListAPIView):
    """
    List all registered companies with status filtering (PENDING, APPROVED, REJECTED, SUSPENDED).
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminCompanyListSerializer

    def get_queryset(self):
        queryset = CompanyProfile.objects.all().select_related('user').order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(verification_status=status_param.upper())
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(company_name__icontains=search) | queryset.filter(email__icontains=search)
        return queryset


@extend_schema(tags=['Admin Module'])
class AdminCompanyDetailView(generics.RetrieveAPIView):
    """
    Retrieve complete company details including legal documents and contact information.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminCompanyDetailSerializer
    queryset = CompanyProfile.objects.all().select_related('user', 'verified_by')


@extend_schema(tags=['Admin Module'])
class AdminCompanyVerifyView(APIView):
    """
    Approve, Reject, or Suspend a company account.
    """
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        try:
            company = CompanyProfile.objects.get(pk=pk)
        except CompanyProfile.DoesNotExist:
            return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminCompanyVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        reason = serializer.validated_data.get('reason', '')

        company.verification_status = new_status
        company.rejection_reason = reason
        company.verified_by = request.user
        company.verified_at = timezone.now()
        company.save()

        # Update user active status if suspended
        if new_status == CompanyProfile.VerificationStatus.SUSPENDED:
            company.user.is_active = False
            company.user.save()
        elif new_status == CompanyProfile.VerificationStatus.APPROVED:
            company.user.is_active = True
            company.user.save()

        return Response({
            'status': 'ok',
            'message': f"Company status successfully updated to {new_status}.",
            'verification_status': company.verification_status,
            'verified_at': company.verified_at
        })


@extend_schema(tags=['Admin Module'])
class AdminVacancyListView(generics.ListAPIView):
    """
    View all posted job vacancies across all registered companies.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminVacancyListSerializer

    def get_queryset(self):
        queryset = Vacancy.objects.all().select_related('company').order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset


@extend_schema(tags=['Admin Module'])
class AdminComplaintListView(generics.ListAPIView):
    """
    View all complaints lodged by users against companies or the system.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminComplaintSerializer

    def get_queryset(self):
        queryset = Complaint.objects.all().select_related('user', 'company', 'replied_by').order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset


@extend_schema(tags=['Admin Module'])
class AdminComplaintReplyView(APIView):
    """
    Respond to a user complaint and mark it as RESOLVED.
    """
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminComplaintReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        complaint.reply = serializer.validated_data['reply']
        complaint.status = serializer.validated_data.get('status', Complaint.Status.RESOLVED)
        complaint.replied_by = request.user
        complaint.replied_at = timezone.now()
        complaint.save()

        return Response({
            'status': 'ok',
            'message': 'Reply submitted and complaint marked as resolved.',
            'complaint_id': complaint.id,
            'status_updated': complaint.status,
            'reply': complaint.reply,
            'replied_at': complaint.replied_at
        })


@extend_schema(tags=['Admin Module'])
class AdminFeedbackListView(generics.ListAPIView):
    """
    View all feedback submitted by users.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminFeedbackSerializer
    queryset = Feedback.objects.all().select_related('user').order_by('-created_at')


@extend_schema(tags=['Admin Module'])
class AdminInterviewMonitorView(generics.ListAPIView):
    """
    Monitor mock interview activities and candidate engagement metrics.
    """
    permission_classes = [IsAdminRole]
    serializer_class = AdminInterviewMonitorSerializer

    def get_queryset(self):
        queryset = AIMockSession.objects.all().select_related('candidate__user').order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset
