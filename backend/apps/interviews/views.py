from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCompanyRole, IsCandidateRole
from .models import InterviewSchedule
from .serializers import (
    InterviewScheduleSerializer,
    InterviewRescheduleSerializer,
    InterviewCancelSerializer,
)


@extend_schema(tags=['Interviews & Scheduling'])
class CompanyInterviewListCreateView(APIView):
    """
    List interviews scheduled by the company or create a new interview schedule.
    Only verified companies can schedule interviews.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        interviews = InterviewSchedule.objects.filter(company=company).order_by('-date', '-start_time')
        
        status_param = request.query_params.get('status')
        if status_param:
            interviews = interviews.filter(status=status_param.upper())
            
        candidate_param = request.query_params.get('candidate_id')
        if candidate_param:
            interviews = interviews.filter(candidate__id=candidate_param)

        serializer = InterviewScheduleSerializer(interviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company or not company.is_verified:
            return Response(
                {'error': 'Only verified companies can schedule interviews.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InterviewScheduleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        interview = serializer.save(company=company)

        return Response({
            'status': 'ok',
            'message': 'Interview scheduled successfully.',
            'interview': InterviewScheduleSerializer(interview).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Interviews & Scheduling'])
class CompanyInterviewDetailView(generics.RetrieveAPIView):
    """
    Retrieve interview schedule details for company.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = InterviewScheduleSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        return InterviewSchedule.objects.filter(company=company)


@extend_schema(tags=['Interviews & Scheduling'])
class CompanyInterviewRescheduleView(APIView):
    """
    Reschedule an existing interview to a new date and time after conflict checking.
    """
    permission_classes = [IsCompanyRole]

    def post(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            interview = InterviewSchedule.objects.get(pk=pk, company=company)
        except InterviewSchedule.DoesNotExist:
            return Response({'error': 'Interview schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

        if interview.status == InterviewSchedule.Status.CANCELLED:
            return Response({'error': 'Cannot reschedule a cancelled interview.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InterviewRescheduleSerializer(data=request.data, context={'interview': interview})
        serializer.is_valid(raise_exception=True)

        interview.date = serializer.validated_data['date']
        interview.start_time = serializer.validated_data['start_time']
        interview.end_time = serializer.validated_data['end_time']
        if 'notes' in serializer.validated_data and serializer.validated_data['notes']:
            interview.notes = serializer.validated_data['notes']
        interview.status = InterviewSchedule.Status.RESCHEDULED
        interview.save()

        return Response({
            'status': 'ok',
            'message': 'Interview rescheduled successfully.',
            'interview': InterviewScheduleSerializer(interview).data
        })


@extend_schema(tags=['Interviews & Scheduling'])
class CompanyInterviewCancelView(APIView):
    """
    Cancel a scheduled interview with an explanation reason.
    """
    permission_classes = [IsCompanyRole]

    def post(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            interview = InterviewSchedule.objects.get(pk=pk, company=company)
        except InterviewSchedule.DoesNotExist:
            return Response({'error': 'Interview schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InterviewCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview.status = InterviewSchedule.Status.CANCELLED
        interview.cancellation_reason = serializer.validated_data['cancellation_reason']
        interview.save()

        return Response({
            'status': 'ok',
            'message': 'Interview cancelled successfully.',
            'cancellation_reason': interview.cancellation_reason,
            'interview_id': interview.id
        })


@extend_schema(tags=['Interviews & Scheduling'])
class CandidateMyInterviewsListView(generics.ListAPIView):
    """
    List all scheduled and completed interviews for the authenticated candidate.
    """
    permission_classes = [IsCandidateRole]
    serializer_class = InterviewScheduleSerializer

    def get_queryset(self):
        candidate = getattr(self.request.user, 'candidate_profile', None)
        return InterviewSchedule.objects.filter(candidate=candidate).order_by('-date', '-start_time')


@extend_schema(tags=['Interviews & Scheduling'])
class CandidateInterviewDetailView(generics.RetrieveAPIView):
    """
    Retrieve specific interview details for the candidate.
    """
    permission_classes = [IsCandidateRole]
    serializer_class = InterviewScheduleSerializer

    def get_queryset(self):
        candidate = getattr(self.request.user, 'candidate_profile', None)
        return InterviewSchedule.objects.filter(candidate=candidate)
