from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCompanyRole, IsCandidateRole, IsVerifiedCompany
from apps.candidates.models import CandidateProfile
from .models import TestSchedule, TestCandidateAssignment
from .serializers import (
    TestScheduleSerializer,
    TestCandidateAssignmentSerializer,
    AssignCandidatesSerializer,
    RecordAttendanceSerializer,
)


@extend_schema(tags=['Tests & Assessments'])
class CompanyTestListCreateView(APIView):
    """
    List company's tests or create a new assessment schedule.
    Only verified companies can schedule tests.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request):
        company = getattr(request.user, 'company_profile', None)
        tests = TestSchedule.objects.filter(company=company).order_by('-date', '-start_time')
        serializer = TestScheduleSerializer(tests, many=True)
        return Response(serializer.data)

    def post(self, request):
        company = getattr(request.user, 'company_profile', None)
        if not company or not company.is_verified:
            return Response({'error': 'Only verified companies can schedule tests.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TestScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        test = serializer.save(company=company)
        return Response({
            'status': 'ok',
            'message': 'Test scheduled successfully.',
            'test': TestScheduleSerializer(test).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Tests & Assessments'])
class CompanyTestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or cancel a test schedule.
    """
    permission_classes = [IsCompanyRole]
    serializer_class = TestScheduleSerializer

    def get_queryset(self):
        company = getattr(self.request.user, 'company_profile', None)
        return TestSchedule.objects.filter(company=company)


@extend_schema(tags=['Tests & Assessments'])
class AssignCandidatesToTestView(APIView):
    """
    Assign a list of eligible candidates to an upcoming test.
    """
    permission_classes = [IsCompanyRole]

    def post(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            test = TestSchedule.objects.get(pk=pk, company=company)
        except TestSchedule.DoesNotExist:
            return Response({'error': 'Test schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignCandidatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate_ids = serializer.validated_data['candidate_ids']

        assigned_count = 0
        for cid in candidate_ids:
            try:
                candidate = CandidateProfile.objects.get(pk=cid)
                TestCandidateAssignment.objects.get_or_create(test=test, candidate=candidate)
                assigned_count += 1
            except CandidateProfile.DoesNotExist:
                continue

        return Response({
            'status': 'ok',
            'message': f"Successfully assigned {assigned_count} candidate(s) to test '{test.test_name}'.",
            'total_assigned': test.candidate_assignments.count()
        })


@extend_schema(tags=['Tests & Assessments'])
class RecordCandidateAttendanceView(APIView):
    """
    Record attendance and assessment score for an assigned candidate.
    """
    permission_classes = [IsCompanyRole]

    def post(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            test = TestSchedule.objects.get(pk=pk, company=company)
        except TestSchedule.DoesNotExist:
            return Response({'error': 'Test schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecordAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cid = serializer.validated_data['candidate_id']
        try:
            assignment = TestCandidateAssignment.objects.get(test=test, candidate__id=cid)
        except TestCandidateAssignment.DoesNotExist:
            return Response({'error': 'Candidate assignment not found for this test.'}, status=status.HTTP_404_NOT_FOUND)

        assignment.attendance_status = serializer.validated_data['attendance_status']
        if 'score' in serializer.validated_data:
            assignment.score = serializer.validated_data['score']
        if 'remarks' in serializer.validated_data:
            assignment.remarks = serializer.validated_data['remarks']
        assignment.save()

        return Response({
            'status': 'ok',
            'message': 'Candidate test score and attendance recorded successfully.',
            'candidate': assignment.candidate.full_name,
            'attendance_status': assignment.attendance_status,
            'score': assignment.score
        })


@extend_schema(tags=['Tests & Assessments'])
class CandidateMyTestsListView(generics.ListAPIView):
    """
    List all assessments and tests scheduled for the authenticated candidate.
    """
    permission_classes = [IsCandidateRole]
    serializer_class = TestScheduleSerializer

    def get_queryset(self):
        candidate = getattr(self.request.user, 'candidate_profile', None)
        return TestSchedule.objects.filter(
            candidate_assignments__candidate=candidate
        ).distinct().order_by('-date', '-start_time')
