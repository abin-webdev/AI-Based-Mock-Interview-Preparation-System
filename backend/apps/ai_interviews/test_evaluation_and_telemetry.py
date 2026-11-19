import io
from PIL import Image
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from apps.ai_interviews.models import AIMockSession, AIMockQuestion, AIMockAnswer, CameraTelemetryReport

User = get_user_model()


class AIMockEvaluationAndTelemetryTests(APITestCase):
    def setUp(self):
        # 1. Candidate 1 (Alice)
        self.user_alice = User.objects.create_user(
            username='alice_dev',
            email='alice@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_alice = CandidateProfile.objects.create(
            user=self.user_alice,
            full_name='Alice Developer',
            phone='9123456789',
            city='Bengaluru',
            state='Karnataka'
        )

        # 2. Company 1 (TechCorp - Applied to)
        self.user_techcorp = User.objects.create_user(
            username='techcorp',
            email='hr@techcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company_techcorp = CompanyProfile.objects.create(
            user=self.user_techcorp,
            company_name='TechCorp Global',
            email='hr@techcorp.com',
            phone='9876543210',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 3. Company 2 (RivalCorp - Not applied to)
        self.user_rival = User.objects.create_user(
            username='rivalcorp',
            email='hr@rivalcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company_rival = CompanyProfile.objects.create(
            user=self.user_rival,
            company_name='RivalCorp',
            email='hr@rivalcorp.com',
            phone='9876543211',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 4. Vacancy and Application to TechCorp
        self.vacancy = Vacancy.objects.create(
            company=self.company_techcorp,
            position='Backend Engineer',
            description='Build microservices.',
            application_deadline=timezone.localdate() + timezone.timedelta(days=15),
            status=Vacancy.Status.ACTIVE
        )
        self.application = Application.objects.create(
            vacancy=self.vacancy,
            candidate=self.candidate_alice,
            status=Application.Status.PENDING
        )

        # 5. Create Alice's Mock Session with 2 questions
        self.session = AIMockSession.objects.create(
            candidate=self.candidate_alice,
            job_role='Django Backend Engineer',
            category=AIMockSession.Category.TECHNICAL,
            difficulty=AIMockSession.Difficulty.MID,
            question_count=2,
            camera_consent_given=True
        )
        self.q1 = AIMockQuestion.objects.create(
            session=self.session,
            question_number=1,
            question_text='How do you optimize Django database queries using select_related and prefetch_related?',
            category='TECHNICAL',
            expected_keywords='select_related, prefetch_related, database hits, SQL joins, query optimization',
            evaluation_rubric='Evaluates understanding of SQL joins for ForeignKeys and separate batch queries for ManyToMany relations.'
        )
        self.q2 = AIMockQuestion.objects.create(
            session=self.session,
            question_number=2,
            question_text='How do you handle background tasks and long-running jobs in Django?',
            category='TECHNICAL',
            expected_keywords='Celery, Redis, message broker, asynchronous, task queue',
            evaluation_rubric='Candidate should mention task queues like Celery, message brokers like Redis, and keeping request-response cycle fast.'
        )

    def test_complete_evaluation_workflow(self):
        """Candidate submits answers to both questions and completes session for AI grading."""
        self.client.force_authenticate(user=self.user_alice)

        # Submit answer to Q1
        self.client.post(
            f'/api/v1/ai-interviews/sessions/{self.session.id}/submit-answer/',
            {
                'question_id': self.q1.id,
                'answer_text': 'I use select_related for single-valued relationships like ForeignKey and OneToOne which performs a SQL join. For many-to-many or reverse foreign keys, I use prefetch_related which executes a separate query and performs Python-side joins, reducing database hits significantly.',
                'time_taken_seconds': 55
            },
            format='json'
        )

        # Submit answer to Q2
        self.client.post(
            f'/api/v1/ai-interviews/sessions/{self.session.id}/submit-answer/',
            {
                'question_id': self.q2.id,
                'answer_text': 'For background jobs, I integrate Celery with Redis as the message broker. Long-running tasks like sending emails or image processing are dispatched asynchronously to worker queues to avoid blocking HTTP requests.',
                'time_taken_seconds': 50
            },
            format='json'
        )

        # Complete interview and trigger evaluation
        complete_resp = self.client.post(f'/api/v1/ai-interviews/sessions/{self.session.id}/complete/')
        self.assertEqual(complete_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_resp.data['status'], 'ok')

        results = complete_resp.data['results']
        self.assertEqual(results['status'], 'COMPLETED')
        self.assertTrue(float(results['overall_score']) >= 65.0)
        self.assertTrue(len(results['summary_feedback']) > 20)
        self.assertTrue(len(results['strengths_summary']) > 10)
        self.assertTrue(len(results['improvements_summary']) > 10)

        # Verify individual question breakdown
        q1_eval = results['questions'][0]['answer']
        self.assertTrue(float(q1_eval['accuracy_score']) >= 6.0)
        self.assertTrue(float(q1_eval['relevance_score']) >= 6.0)
        self.assertTrue(float(q1_eval['overall_question_score']) >= 60.0)
        self.assertTrue(len(q1_eval['feedback']) > 15)

    def test_camera_telemetry_recording(self):
        """Candidate uploads camera telemetry metrics with consent."""
        self.client.force_authenticate(user=self.user_alice)
        payload = {
            'consent_given': True,
            'frames_processed': 150,
            'centered_posture_percentage': 92.5,
            'head_stability_score': 88.0,
            'eye_contact_ratio': 85.0
        }
        response = self.client.post(
            f'/api/v1/ai-interviews/sessions/{self.session.id}/camera-telemetry/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

        telemetry = response.data['telemetry']
        self.assertEqual(float(telemetry['centered_posture_percentage']), 92.5)
        self.assertEqual(float(telemetry['head_stability_score']), 88.0)
        self.assertIn('advisory', telemetry['disclaimer'].lower())

    def test_camera_frame_image_processing(self):
        """Uploading an image frame to camera telemetry triggers OpenCV processing."""
        self.client.force_authenticate(user=self.user_alice)

        # Generate a small in-memory RGB image
        img = Image.new('RGB', (320, 240), color=(180, 180, 180))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        img_io.name = 'frame.jpg'

        response = self.client.post(
            f'/api/v1/ai-interviews/sessions/{self.session.id}/camera-telemetry/',
            {'frame_image': img_io, 'consent_given': True},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CameraTelemetryReport.objects.filter(session=self.session).exists())

    def test_results_endpoint_for_candidate(self):
        """Candidate can inspect their comprehensive results report."""
        self.client.force_authenticate(user=self.user_alice)
        self.client.post(f'/api/v1/ai-interviews/sessions/{self.session.id}/complete/')

        response = self.client.get(f'/api/v1/ai-interviews/sessions/{self.session.id}/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.session.id)
        self.assertEqual(response.data['candidate_name'], 'Alice Developer')

    def test_company_access_control_for_candidate_results(self):
        """
        TechCorp (to which candidate applied) CAN view candidate's interview results.
        RivalCorp (no application) is REJECTED with 403 Forbidden.
        """
        # Ensure session is completed
        self.session.status = AIMockSession.Status.COMPLETED
        self.session.overall_score = 82.0
        self.session.save()

        # 1. TechCorp access (Authorized)
        self.client.force_authenticate(user=self.user_techcorp)
        auth_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.session.id}/company-results/')
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_resp.data['candidate_name'], 'Alice Developer')

        # 2. RivalCorp access (Unauthorized - 403 Forbidden)
        self.client.force_authenticate(user=self.user_rival)
        unauth_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.session.id}/company-results/')
        self.assertEqual(unauth_resp.status_code, status.HTTP_403_FORBIDDEN)
