import io
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from apps.ai_interviews.models import AIMockSession

User = get_user_model()


class EndToEndSecurityAndRBACValidationTests(APITestCase):
    def setUp(self):
        # 1. Admin
        self.admin_user = User.objects.create_superuser(
            username='admin_security',
            email='admin@security.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # 2. Candidate 1 (Alice)
        self.user_alice = User.objects.create_user(
            username='alice_sec',
            email='alice@security.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_alice = CandidateProfile.objects.create(
            user=self.user_alice,
            full_name='Alice Security',
            phone='9123456789',
            city='Bengaluru',
            state='Karnataka'
        )

        # 3. Candidate 2 (Bob)
        self.user_bob = User.objects.create_user(
            username='bob_sec',
            email='bob@security.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_bob = CandidateProfile.objects.create(
            user=self.user_bob,
            full_name='Bob Security',
            phone='9123456780',
            city='Mumbai',
            state='Maharashtra'
        )

        # 4. Verified Company (AlphaCorp)
        self.user_alpha = User.objects.create_user(
            username='alphacorp',
            email='hr@alphacorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company_alpha = CompanyProfile.objects.create(
            user=self.user_alpha,
            company_name='AlphaCorp',
            email='hr@alphacorp.com',
            phone='9876543210',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 5. Unverified Company (PendingCorp)
        self.user_pending = User.objects.create_user(
            username='pendingcorp',
            email='hr@pendingcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company_pending = CompanyProfile.objects.create(
            user=self.user_pending,
            company_name='PendingCorp',
            email='hr@pendingcorp.com',
            phone='9876543211',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )

        # 6. Unrelated Company (RivalCorp)
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
            phone='9876543212',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # Vacancy & Application: Alice applies to AlphaCorp
        self.vacancy = Vacancy.objects.create(
            company=self.company_alpha,
            position='Software Architect',
            description='Design distributed systems.',
            application_deadline=timezone.localdate() + timezone.timedelta(days=20),
            status=Vacancy.Status.ACTIVE
        )
        self.alice_application = Application.objects.create(
            vacancy=self.vacancy,
            candidate=self.candidate_alice,
            status=Application.Status.PENDING
        )

        # Alice's Mock Session
        self.alice_session = AIMockSession.objects.create(
            candidate=self.candidate_alice,
            job_role='Software Architect',
            category=AIMockSession.Category.TECHNICAL,
            difficulty=AIMockSession.Difficulty.SENIOR,
            question_count=2,
            status=AIMockSession.Status.COMPLETED,
            overall_score=85.0
        )

    def test_anonymous_access_is_blocked_on_protected_endpoints(self):
        """Unauthenticated requests to protected endpoints return 401 Unauthorized."""
        endpoints = [
            '/api/v1/admin/dashboard-stats/',
            '/api/v1/candidates/profile/',
            '/api/v1/companies/profile/',
            '/api/v1/applications/',
            '/api/v1/ai-interviews/sessions/',
            '/api/v1/feedback/',
            '/api/v1/complaints/',
            '/api/v1/notifications/',
        ]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Expected 401 on {url}, got {response.status_code}"
            )

    def test_cross_role_access_control(self):
        """Role-Based Access Control: Candidates cannot access Admin or Company views."""
        self.client.force_authenticate(user=self.user_alice)

        # 1. Candidate hitting Admin dashboard
        admin_resp = self.client.get('/api/v1/admin/dashboard-stats/')
        self.assertEqual(admin_resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Candidate hitting Company vacancy creation
        vacancy_resp = self.client.post('/api/v1/companies/vacancies/', {
            'position': 'Hacker',
            'description': 'Attempting unauthorized post.'
        }, format='json')
        self.assertEqual(vacancy_resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Company user hitting Candidate profile
        self.client.force_authenticate(user=self.user_alpha)
        cand_resp = self.client.get('/api/v1/candidates/profile/')
        self.assertEqual(cand_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unverified_company_restricted_from_privileged_actions(self):
        """Unverified company cannot post vacancies or schedule tests."""
        self.client.force_authenticate(user=self.user_pending)

        # Post vacancy
        vac_resp = self.client.post('/api/v1/companies/vacancies/', {
            'position': 'Developer',
            'description': 'Should be rejected.'
        }, format='json')
        self.assertEqual(vac_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Schedule test
        test_resp = self.client.post('/api/v1/tests/', {
            'test_name': 'Pending Exam',
            'test_type': 'TECHNICAL',
            'date': str(timezone.localdate() + timezone.timedelta(days=2)),
            'start_time': '10:00:00',
            'end_time': '11:00:00'
        }, format='json')
        self.assertEqual(test_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_object_level_application_isolation(self):
        """Object-Level Authorization: Bob cannot withdraw or access Alice's application."""
        self.client.force_authenticate(user=self.user_bob)

        # Bob tries to withdraw Alice's application
        withdraw_resp = self.client.post(f'/api/v1/applications/{self.alice_application.id}/withdraw/')
        self.assertIn(withdraw_resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        self.alice_application.refresh_from_db()
        self.assertEqual(self.alice_application.status, Application.Status.PENDING)

    def test_object_level_mock_session_and_results_isolation(self):
        """Bob cannot access Alice's mock interview session or results."""
        self.client.force_authenticate(user=self.user_bob)

        # Bob views Alice's session
        session_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.alice_session.id}/')
        self.assertEqual(session_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Bob views Alice's results
        results_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.alice_session.id}/results/')
        self.assertEqual(results_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_company_cannot_view_candidate_results(self):
        """
        RivalCorp (Alice never applied here) is REJECTED from viewing Alice's mock interview results.
        AlphaCorp (Alice applied here) is AUTHORIZED.
        """
        # RivalCorp (Unauthorized)
        self.client.force_authenticate(user=self.user_rival)
        rival_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.alice_session.id}/company-results/')
        self.assertEqual(rival_resp.status_code, status.HTTP_403_FORBIDDEN)

        # AlphaCorp (Authorized)
        self.client.force_authenticate(user=self.user_alpha)
        alpha_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{self.alice_session.id}/company-results/')
        self.assertEqual(alpha_resp.status_code, status.HTTP_200_OK)

    def test_secure_file_upload_validation(self):
        """Disallows dangerous file extensions (.exe, .sh) on resume and photo endpoints."""
        self.client.force_authenticate(user=self.user_alice)

        # 1. Disallow .exe as resume
        bad_resume = SimpleUploadedFile("malware.exe", b"MZexecutabledata", content_type="application/x-msdownload")
        resume_resp = self.client.post('/api/v1/candidates/profile/resume/', {'resume': bad_resume}, format='multipart')
        self.assertEqual(resume_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('resume', resume_resp.data)

        # 2. Disallow .sh as profile photo
        bad_photo = SimpleUploadedFile("script.sh", b"#!/bin/bash\necho hi", content_type="application/x-sh")
        photo_resp = self.client.post('/api/v1/candidates/profile/photo/', {'photo': bad_photo}, format='multipart')
        self.assertEqual(photo_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', photo_resp.data)

    def test_camera_telemetry_consent_protection(self):
        """Camera telemetry endpoint rejects requests where candidate consent is not given."""
        self.client.force_authenticate(user=self.user_alice)
        payload = {
            'consent_given': False,
            'centered_posture_percentage': 85.0
        }
        response = self.client.post(
            f'/api/v1/ai-interviews/sessions/{self.alice_session.id}/camera-telemetry/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('consent', str(response.data).lower())

    def test_password_and_email_validation(self):
        """Registration rejects weak passwords and malformed emails."""
        # 1. Weak password
        weak_pwd_resp = self.client.post('/api/v1/auth/register/candidate/', {
            'email': 'valid.candidate@example.com',
            'username': 'validcand',
            'password': '123',
            'full_name': 'Valid Candidate',
            'phone': '9876543210'
        }, format='json')
        self.assertEqual(weak_pwd_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Malformed email
        bad_email_resp = self.client.post('/api/v1/auth/register/candidate/', {
            'email': 'not-an-email',
            'username': 'bademailcand',
            'password': 'StrongPassword123!',
            'full_name': 'Bad Email',
            'phone': '9876543210'
        }, format='json')
        self.assertEqual(bad_email_resp.status_code, status.HTTP_400_BAD_REQUEST)
