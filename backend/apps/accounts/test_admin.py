from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.complaints.models import Complaint
from apps.feedback.models import Feedback
from apps.vacancies.models import Vacancy
from apps.ai_interviews.models import AIMockSession
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AdminModulePhase4Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@interviews.org',
            username='systemadmin',
            password='AdminPassword123!',
            role=User.Role.ADMIN
        )

        # Candidate user
        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',
            username='candidate_bob',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Bob Candidate'
        )

        # Company user 1: Pending
        self.pending_company_user = User.objects.create_user(
            email='hr@startup.com',
            username='startup_co',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.pending_company = CompanyProfile.objects.create(
            user=self.pending_company_user,
            company_name='Startup Co',
            phone='1234567890',
            address='Indiranagar',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )

        # Company user 2: Approved
        self.approved_company_user = User.objects.create_user(
            email='hr@acme.com',
            username='acme_corp',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.approved_company = CompanyProfile.objects.create(
            user=self.approved_company_user,
            company_name='Acme Corp',
            phone='0987654321',
            address='Whitefield',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # Vacancy
        self.vacancy = Vacancy.objects.create(
            company=self.approved_company,
            position='Django Backend Architect',
            description='Lead backend design and APIs.',
            application_deadline=timezone.now().date() + timedelta(days=30)
        )

        # Complaint
        self.complaint = Complaint.objects.create(
            user=self.candidate_user,
            company=self.approved_company,
            complaint_text='Interview schedule delay without notice.'
        )

        # Feedback
        self.feedback = Feedback.objects.create(
            user=self.candidate_user,
            feedback_text='Mock interview questions are very relevant.'
        )

        # AI Mock Session
        self.session = AIMockSession.objects.create(
            candidate=self.candidate_profile,
            job_role='Django Developer',
            status=AIMockSession.Status.COMPLETED
        )

    # 1. Dashboard Statistics
    def test_admin_dashboard_stats_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['users']['total'], 4)
        self.assertEqual(data['companies']['pending'], 1)
        self.assertEqual(data['companies']['approved'], 1)
        self.assertEqual(data['vacancies']['total'], 1)
        self.assertEqual(data['complaints']['pending'], 1)
        self.assertEqual(data['feedback']['total'], 1)
        self.assertEqual(data['ai_interviews']['completed'], 1)

    def test_non_admin_forbidden_from_dashboard(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/v1/admin/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 2. User Management
    def test_admin_list_users(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/users/?role=CANDIDATE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['email'], 'candidate@example.com')

    def test_admin_toggle_user_active(self):
        self.client.force_authenticate(user=self.admin_user)
        # Deactivate candidate
        response = self.client.post(f'/api/v1/admin/users/{self.candidate_user.id}/toggle-active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_user.refresh_from_db()
        self.assertFalse(self.candidate_user.is_active)

        # Reactivate candidate
        response = self.client.post(f'/api/v1/admin/users/{self.candidate_user.id}/toggle-active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_user.refresh_from_db()
        self.assertTrue(self.candidate_user.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/admin/users/{self.admin_user.id}/toggle-active/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 3. Company Management & Verification
    def test_admin_list_companies(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/companies/?status=PENDING')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['company_name'], 'Startup Co')

    def test_admin_approve_company(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/admin/companies/{self.pending_company.id}/verify/', {
            'status': 'APPROVED'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_company.refresh_from_db()
        self.assertEqual(self.pending_company.verification_status, 'APPROVED')
        self.assertTrue(self.pending_company.is_verified)
        self.assertEqual(self.pending_company.verified_by, self.admin_user)

    def test_admin_reject_company(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/admin/companies/{self.pending_company.id}/verify/', {
            'status': 'REJECTED',
            'reason': 'Incomplete corporate registration documents.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_company.refresh_from_db()
        self.assertEqual(self.pending_company.verification_status, 'REJECTED')
        self.assertEqual(self.pending_company.rejection_reason, 'Incomplete corporate registration documents.')

    def test_admin_suspend_company_deactivates_user(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/admin/companies/{self.approved_company.id}/verify/', {
            'status': 'SUSPENDED',
            'reason': 'Policy violation.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approved_company.refresh_from_db()
        self.approved_company_user.refresh_from_db()
        self.assertEqual(self.approved_company.verification_status, 'SUSPENDED')
        self.assertFalse(self.approved_company_user.is_active)

    # 4. Vacancy Audit
    def test_admin_list_vacancies(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/vacancies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['position'], 'Django Backend Architect')

    # 5. Complaints Management & Reply
    def test_admin_list_complaints(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/complaints/?status=PENDING')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_admin_reply_to_complaint(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/admin/complaints/{self.complaint.id}/reply/', {
            'reply': 'We have contacted the company HR and your rescheduled slot is confirmed.',
            'status': 'RESOLVED'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'RESOLVED')
        self.assertEqual(self.complaint.reply, 'We have contacted the company HR and your rescheduled slot is confirmed.')
        self.assertEqual(self.complaint.replied_by, self.admin_user)
        self.assertIsNotNone(self.complaint.replied_at)

    # 6. Feedback View
    def test_admin_view_feedback(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/feedback/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    # 7. Interview Activity Monitoring
    def test_admin_interview_monitor(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/admin/interview-monitor/?status=COMPLETED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['candidate_name'], 'Bob Candidate')
