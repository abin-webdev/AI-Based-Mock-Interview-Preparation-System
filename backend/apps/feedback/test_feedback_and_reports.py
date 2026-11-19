from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile
from apps.feedback.models import Feedback
from apps.complaints.models import Complaint
from apps.notifications.models import Notification
from apps.ai_interviews.models import AIMockSession, AIMockQuestion, AIMockAnswer

User = get_user_model()


class FeedbackComplaintsNotificationsAndReportsTests(APITestCase):
    def setUp(self):
        # 1. Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            email='admin@mockinterview.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # 2. Candidate User & Profile
        self.candidate_user = User.objects.create_user(
            username='alice_candidate',
            email='alice@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Alice Candidate',
            phone='9123456789',
            city='Bengaluru',
            state='Karnataka'
        )

        # 3. Another Candidate User
        self.other_candidate = User.objects.create_user(
            username='bob_candidate',
            email='bob@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )

        # 4. Company User & Profile
        self.company_user = User.objects.create_user(
            username='techcorp',
            email='hr@techcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='TechCorp Global',
            email='hr@techcorp.com',
            phone='9876543210',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 5. Completed Mock Session for PDF testing
        self.session = AIMockSession.objects.create(
            candidate=self.candidate_profile,
            job_role='Senior Python Engineer',
            category=AIMockSession.Category.TECHNICAL,
            difficulty=AIMockSession.Difficulty.SENIOR,
            question_count=1,
            overall_score=88.5,
            summary_feedback='Excellent technical depth and architectural reasoning.',
            strengths_summary='Clean code principles and database indexing.',
            improvements_summary='Discuss distributed transaction boundaries.',
            status=AIMockSession.Status.COMPLETED,
            completed_at=timezone.now()
        )
        self.q1 = AIMockQuestion.objects.create(
            session=self.session,
            question_number=1,
            question_text='Explain how database indexing works in PostgreSQL.',
            category='TECHNICAL',
            expected_keywords='B-Tree, GIN, index scan, latency',
            evaluation_rubric='Evaluates understanding of B-Tree indexing and query planner optimization.'
        )
        AIMockAnswer.objects.create(
            session=self.session,
            question=self.q1,
            candidate=self.candidate_profile,
            answer_text='PostgreSQL uses B-Tree indexes by default which provide O(log n) lookup times for equality and range queries, reducing full table sequential scans.',
            overall_question_score=88.5,
            feedback='Strong, technically accurate answer.',
            strengths='Correctly cited B-Tree and logarithmic complexity.',
            improvement_areas='Mention partial and composite indexes.'
        )

    def test_feedback_submission_and_list(self):
        """Candidate submits feedback and lists their submitted feedbacks."""
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.post('/api/v1/feedback/', {
            'feedback_text': 'The AI interview feedback was extremely insightful!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['feedback_text'], 'The AI interview feedback was extremely insightful!')

        # List feedback
        list_resp = self.client.get('/api/v1/feedback/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        results = list_resp.data['results'] if 'results' in list_resp.data else list_resp.data
        self.assertEqual(len(results), 1)

    def test_complaint_lifecycle_and_admin_reply(self):
        """Candidate files complaint, admin replies, status updates to RESOLVED."""
        self.client.force_authenticate(user=self.candidate_user)
        # 1. File Complaint
        create_resp = self.client.post('/api/v1/complaints/', {
            'company_id': self.company_profile.id,
            'complaint_text': 'Interview rescheduled without prior notification.'
        }, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        complaint_id = create_resp.data['id']

        complaint = Complaint.objects.get(id=complaint_id)
        self.assertEqual(complaint.status, Complaint.Status.PENDING)

        # 2. Admin replies to complaint
        self.client.force_authenticate(user=self.admin_user)
        reply_resp = self.client.post(f'/api/v1/admin/complaints/{complaint_id}/reply/', {
            'reply': 'We have contacted TechCorp HR and requested them to maintain minimum 24hr notice.',
            'status': 'RESOLVED'
        }, format='json')
        self.assertEqual(reply_resp.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertIn('TechCorp HR', complaint.reply)
        self.assertEqual(complaint.replied_by, self.admin_user)

    def test_notifications_workflow(self):
        """User receives notification, inspects list, and marks as read."""
        notif = Notification.objects.create(
            user=self.candidate_user,
            title='Interview Scheduled',
            message='Your technical interview with TechCorp is confirmed.',
            notification_type=Notification.NotificationType.INTERVIEW
        )

        self.client.force_authenticate(user=self.candidate_user)
        list_resp = self.client.get('/api/v1/notifications/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        results = list_resp.data['results'] if 'results' in list_resp.data else list_resp.data
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['is_read'])

        # Mark single as read
        read_resp = self.client.post(f'/api/v1/notifications/{notif.id}/read/')
        self.assertEqual(read_resp.status_code, status.HTTP_200_OK)

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # Mark all read
        mark_all_resp = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(mark_all_resp.status_code, status.HTTP_200_OK)

    def test_pdf_report_generation(self):
        """Candidate downloads professional PDF report card using ReportLab."""
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get(f'/api/v1/reports/mock-interviews/{self.session.id}/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))

        # Unauthorized candidate cannot download another's PDF
        self.client.force_authenticate(user=self.other_candidate)
        unauth_resp = self.client.get(f'/api/v1/reports/mock-interviews/{self.session.id}/pdf/')
        self.assertEqual(unauth_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_legacy_flutter_send_feedback_endpoint(self):
        """Matches Flutter send_feedback.dart: POST /myapp/send_feedback/"""
        response = self.client.post(
            '/myapp/send_feedback/',
            {
                'feedback': 'Great mobile mock interview user experience!',
                'lid': str(self.candidate_user.id)
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertTrue(Feedback.objects.filter(user=self.candidate_user).exists())

    def test_legacy_flutter_send_complaint_and_view_reply_endpoints(self):
        """Matches Flutter send_complaint.dart and view_reply.dart"""
        # 1. Send Complaint
        send_resp = self.client.post(
            '/myapp/send_complaint/',
            {
                'complaint': 'Audio quality issue during the test.',
                'lid': str(self.candidate_user.id),
                'company': str(self.company_profile.id)
            },
            format='multipart'
        )
        self.assertEqual(send_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(send_resp.data['status'], 'ok')

        complaint = Complaint.objects.get(user=self.candidate_user)
        complaint.reply = 'We have inspected the server audio codecs and resolved the issue.'
        complaint.status = Complaint.Status.RESOLVED
        complaint.save()

        # 2. View Reply (Flutter view_reply.dart)
        reply_resp = self.client.post(
            '/myapp/user_viewreply/',
            {'lid': str(self.candidate_user.id)},
            format='multipart'
        )
        self.assertEqual(reply_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(reply_resp.data['status'], 'ok')

        # Check 'key' array expected by Flutter
        self.assertIn('key', reply_resp.data)
        self.assertTrue(len(reply_resp.data['key']) >= 1)

        first_item = reply_resp.data['key'][0]
        self.assertEqual(first_item['id'], str(complaint.id))
        self.assertEqual(first_item['complaint'], 'Audio quality issue during the test.')
        self.assertIn('audio codecs', first_item['reply'])
        self.assertIn('audio codecs', first_item['replay'])
        self.assertEqual(first_item['status'], 'Resolved')
