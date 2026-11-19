from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsCandidateRole, IsCompanyRole
from apps.applications.models import Application
from .models import AIMockSession, AIMockQuestion, AIMockAnswer, CameraTelemetryReport
from .serializers import (
    AIMockSessionSerializer,
    CreateAIMockSessionSerializer,
    AIMockQuestionSerializer,
    AIMockAnswerSerializer,
    SubmitAnswerSerializer,
    CameraTelemetryReportSerializer,
    UploadCameraTelemetrySerializer,
    AIMockInterviewResultsSerializer,
)
from .services import generate_mock_interview_questions
from .evaluation_service import evaluate_mock_session
from .camera_service import record_camera_telemetry


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSessionListCreateView(APIView):
    """
    List all mock interview sessions for the authenticated candidate,
    or create a new session with dynamically generated questions.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        sessions = AIMockSession.objects.filter(candidate=candidate).order_by('-created_at')
        serializer = AIMockSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        candidate = getattr(request.user, 'candidate_profile', None)
        if not candidate:
            return Response({'error': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CreateAIMockSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = serializer.save(candidate=candidate)

        # Dynamically generate questions via NLP / Gemini
        questions = generate_mock_interview_questions(session)

        return Response({
            'status': 'ok',
            'message': f'Mock interview session created with {len(questions)} dynamically generated questions.',
            'session': AIMockSessionSerializer(session).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSessionDetailView(APIView):
    """
    Retrieve full session information, questions, and submitted answers.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AIMockSessionSerializer(session)
        return Response(serializer.data)


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSessionStartView(APIView):
    """
    Begin the mock interview session. Marks status as IN_PROGRESS and tracks start timestamp.
    """
    permission_classes = [IsCandidateRole]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if session.status == AIMockSession.Status.COMPLETED:
            return Response({'error': 'Session already completed.'}, status=status.HTTP_400_BAD_REQUEST)

        if not session.started_at:
            session.started_at = timezone.now()
        session.status = AIMockSession.Status.IN_PROGRESS
        session.save()

        return Response({
            'status': 'ok',
            'message': 'Mock interview session started.',
            'session_id': session.id,
            'started_at': session.started_at
        })


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSessionQuestionsListView(APIView):
    """
    Retrieve all questions generated for this mock interview session.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        questions = session.questions.all().order_by('question_number')
        serializer = AIMockQuestionSerializer(questions, many=True)
        return Response(serializer.data)


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSubmitAnswerView(APIView):
    """
    Submit candidate answer for a specific question within this interview session.
    """
    permission_classes = [IsCandidateRole]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if session.status == AIMockSession.Status.COMPLETED:
            return Response({'error': 'Cannot submit answers to a completed session.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_id = serializer.validated_data['question_id']
        try:
            question = AIMockQuestion.objects.get(pk=question_id, session=session)
        except AIMockQuestion.DoesNotExist:
            return Response({'error': 'Question does not belong to this session.'}, status=status.HTTP_404_NOT_FOUND)

        # Update existing answer or create new one
        answer, created = AIMockAnswer.objects.update_or_create(
            session=session,
            question=question,
            defaults={
                'candidate': candidate,
                'answer_text': serializer.validated_data['answer_text'],
                'time_taken_seconds': serializer.validated_data.get('time_taken_seconds', 0),
            }
        )

        # Auto-update session status to IN_PROGRESS if not already
        if session.status == AIMockSession.Status.CREATED:
            session.status = AIMockSession.Status.IN_PROGRESS
            if not session.started_at:
                session.started_at = timezone.now()
            session.save()

        return Response({
            'status': 'ok',
            'message': 'Answer submitted successfully.',
            'answer': AIMockAnswerSerializer(answer).data,
            'total_answered': session.answers.count(),
            'total_questions': session.questions.count()
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@extend_schema(tags=['AI Mock Interviews'])
class CandidateAbandonSessionView(APIView):
    """
    Abandon an in-progress mock interview session.
    """
    permission_classes = [IsCandidateRole]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        session.status = AIMockSession.Status.ABANDONED
        session.save()

        return Response({
            'status': 'ok',
            'message': 'Mock interview session has been abandoned.'
        })


@extend_schema(tags=['AI Mock Interviews'])
class CandidateCompleteSessionView(APIView):
    """
    Submits the interview for final multi-criteria AI grading.
    Evaluates all submitted answers, calculates score (0-100),
    and synthesizes overall feedback, strengths, and areas for improvement.
    """
    permission_classes = [IsCandidateRole]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if session.status == AIMockSession.Status.COMPLETED:
            # Already completed, return existing results
            serializer = AIMockInterviewResultsSerializer(session)
            return Response({
                'status': 'ok',
                'message': 'Session is already evaluated and completed.',
                'results': serializer.data
            })

        # Run AI Evaluation engine
        summary_result = evaluate_mock_session(session)

        # Re-fetch session with all evaluated relations
        session.refresh_from_db()
        serializer = AIMockInterviewResultsSerializer(session)

        return Response({
            'status': 'ok',
            'message': 'Mock interview evaluated and completed successfully.',
            'summary': summary_result,
            'results': serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(tags=['AI Mock Interviews'])
class CandidateUploadCameraTelemetryView(APIView):
    """
    Upload optional, privacy-conscious camera telemetry snapshot or metrics.
    Enforces candidate consent check.
    """
    permission_classes = [IsCandidateRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UploadCameraTelemetrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consent_given = serializer.validated_data.get('consent_given', True)
        if not consent_given:
            return Response(
                {'error': 'Telemetry collection requires candidate consent.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        frame_bytes = None
        if 'frame_image' in request.FILES:
            frame_bytes = request.FILES['frame_image'].read()

        try:
            report = record_camera_telemetry(
                session=session,
                candidate=candidate,
                consent_given=consent_given,
                telemetry_data=serializer.validated_data,
                frame_bytes=frame_bytes
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'ok',
            'message': 'Camera telemetry recorded successfully.',
            'telemetry': CameraTelemetryReportSerializer(report).data
        })


@extend_schema(tags=['AI Mock Interviews'])
class CandidateSessionResultsView(APIView):
    """
    Retrieve comprehensive evaluation report card for the candidate's completed mock interview.
    """
    permission_classes = [IsCandidateRole]

    def get(self, request, pk):
        candidate = getattr(request.user, 'candidate_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk, candidate=candidate)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Mock session not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AIMockInterviewResultsSerializer(session)
        return Response(serializer.data)


@extend_schema(tags=['AI Mock Interviews'])
class CompanyCandidateInterviewResultsView(APIView):
    """
    Allows an authorized company to view relevant candidate mock interview results
    ONLY if the candidate has submitted an application for one of the company's vacancies.
    Prevents unauthorized access to candidate records.
    """
    permission_classes = [IsCompanyRole]

    def get(self, request, pk):
        company = getattr(request.user, 'company_profile', None)
        try:
            session = AIMockSession.objects.get(pk=pk)
        except AIMockSession.DoesNotExist:
            return Response({'error': 'Interview session not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check authorization: Candidate must have applied to this company
        has_applied = Application.objects.filter(
            candidate=session.candidate,
            vacancy__company=company
        ).exists()

        if not has_applied and not request.user.is_staff:
            return Response(
                {'error': 'Unauthorized. You can only view mock interview reports for candidates who have applied to your vacancies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AIMockInterviewResultsSerializer(session)
        return Response(serializer.data)

