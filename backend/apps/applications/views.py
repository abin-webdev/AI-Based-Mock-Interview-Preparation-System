from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCandidateRole
from .models import Application
from .serializers import (
    CandidateApplicationListSerializer,
    CandidateApplicationDetailSerializer,
)


@extend_schema(tags=['Job Applications'])
class MyApplicationsListView(generics.ListAPIView):
    """
    List all job applications submitted by the authenticated candidate.
    """
    permission_classes = [IsCandidateRole]
    serializer_class = CandidateApplicationListSerializer

    def get_queryset(self):
        candidate = getattr(self.request.user, 'candidate_profile', None)
        return Application.objects.filter(candidate=candidate).select_related(
            'vacancy__company'
        ).order_by('-applied_at')


@extend_schema(tags=['Job Applications'])
class ApplicationDetailView(generics.RetrieveAPIView):
    """
    View details and status of a specific job application.
    """
    permission_classes = [IsCandidateRole]
    serializer_class = CandidateApplicationDetailSerializer

    def get_queryset(self):
        candidate = getattr(self.request.user, 'candidate_profile', None)
        return Application.objects.filter(candidate=candidate).select_related('vacancy__company')


@extend_schema(tags=['Job Applications'])
class ApplicationWithdrawView(APIView):
    """
    Withdraw a pending job application.
    """
    permission_classes = [IsCandidateRole]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            application = Application.objects.get(pk=pk, candidate=candidate)
        except Application.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.status != Application.Status.PENDING:
            return Response({
                'error': f"Cannot withdraw an application with status '{application.status}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        application.delete()
        return Response({
            'status': 'ok',
            'message': 'Application successfully withdrawn.'
        })
