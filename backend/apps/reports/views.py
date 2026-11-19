from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema

from apps.ai_interviews.models import AIMockSession
from apps.applications.models import Application
from .pdf_generator import generate_mock_interview_pdf


@extend_schema(tags=['Reports & PDFs'])
class AIMockInterviewPDFReportView(APIView):
    """
    Download a formatted, professional PDF Evaluation Report for an AI Mock Interview Session.
    Authorized for the candidate who completed the interview, companies the candidate applied to, or administrators.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            session = AIMockSession.objects.select_related('candidate__user').prefetch_related('questions__answer').get(pk=pk)
        except AIMockSession.DoesNotExist:
            return HttpResponse('Mock interview session not found.', status=status.HTTP_404_NOT_FOUND)

        # Permission check
        user = request.user
        is_candidate_owner = (hasattr(user, 'candidate_profile') and session.candidate == user.candidate_profile)
        is_admin = user.is_staff or user.role == 'ADMIN'
        is_authorized_company = False

        if hasattr(user, 'company_profile'):
            is_authorized_company = Application.objects.filter(
                candidate=session.candidate,
                vacancy__company=user.company_profile
            ).exists()

        if not (is_candidate_owner or is_admin or is_authorized_company):
            return HttpResponse('Unauthorized access to candidate report.', status=status.HTTP_403_FORBIDDEN)

        pdf_buffer = generate_mock_interview_pdf(session)

        filename = f"Mock_Interview_Report_Session_{session.id}.pdf"
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
