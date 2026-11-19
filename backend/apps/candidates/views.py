from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCandidateRole
from apps.applications.models import Application
from apps.ai_interviews.models import AIMockSession
from .models import CandidateProfile
from .serializers import (
    CandidateProfileSerializer,
    CandidateProfileUpdateSerializer,
    CandidatePhotoUploadSerializer,
    CandidateResumeUploadSerializer,
)


@extend_schema(tags=['Candidate Portal'])
class CandidateDashboardView(APIView):
    """
    Returns aggregated metrics and statistics for the candidate's dashboard.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        applications = Application.objects.filter(candidate=candidate)
        total_applied = applications.count()
        pending_apps = applications.filter(status='PENDING').count()
        shortlisted_apps = applications.filter(status='SHORTLISTED').count()
        accepted_apps = applications.filter(status='ACCEPTED').count()
        rejected_apps = applications.filter(status='REJECTED').count()

        mock_sessions = AIMockSession.objects.filter(candidate=candidate)
        total_sessions = mock_sessions.count()
        completed_sessions = mock_sessions.filter(status='COMPLETED').count()

        # Compute profile completeness
        fields_to_check = [
            candidate.full_name, candidate.phone, candidate.dob,
            candidate.city, candidate.state, candidate.photo,
            candidate.resume, candidate.qualifications, candidate.skills
        ]
        completed_fields = sum(1 for f in fields_to_check if f)
        completion_pct = int((completed_fields / len(fields_to_check)) * 100)

        return Response({
            'candidate': {
                'id': candidate.id,
                'full_name': candidate.full_name,
                'email': request.user.email,
                'profile_completeness_percentage': completion_pct,
                'has_resume': bool(candidate.resume),
                'has_photo': bool(candidate.photo),
            },
            'applications': {
                'total_applied': total_applied,
                'pending': pending_apps,
                'shortlisted': shortlisted_apps,
                'accepted': accepted_apps,
                'rejected': rejected_apps,
            },
            'ai_interviews': {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
            }
        })


@extend_schema(tags=['Candidate Portal'])
class CandidateProfileView(APIView):
    """
    Retrieve and update the authenticated candidate's profile.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CandidateProfileSerializer(candidate)
        return Response(serializer.data)

    def put(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CandidateProfileUpdateSerializer(candidate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'ok',
            'message': 'Profile updated successfully.',
            'profile': CandidateProfileSerializer(candidate).data
        })


@extend_schema(tags=['Candidate Portal'])
class CandidatePhotoUploadView(APIView):
    """
    Upload or update candidate profile photo.
    """
    permission_classes = [IsCandidateRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CandidatePhotoUploadSerializer(candidate, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        photo_url = candidate.photo.url if candidate.photo else None
        return Response({
            'status': 'ok',
            'message': 'Profile photo uploaded successfully.',
            'photo_url': photo_url
        })


@extend_schema(tags=['Candidate Portal'])
class CandidateResumeUploadView(APIView):
    """
    Upload, replace, or delete candidate resume PDF.
    """
    permission_classes = [IsCandidateRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CandidateResumeUploadSerializer(candidate, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        resume_url = candidate.resume.url if candidate.resume else None
        return Response({
            'status': 'ok',
            'message': 'Resume uploaded successfully.',
            'resume_url': resume_url
        })

    def delete(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if candidate.resume:
            candidate.resume.delete(save=True)

        return Response({
            'status': 'ok',
            'message': 'Resume deleted successfully.'
        })
