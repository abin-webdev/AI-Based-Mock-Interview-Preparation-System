import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application

User = get_user_model()


class CandidateModulePhase6Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Candidate 1 (Alice)
        self.candidate_user = User.objects.create_user(
            email='alice@example.com',
            username='alice',
            password='CandidatePassword123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Alice Smith',
            phone='+1-555-1001',
            city='Seattle',
            state='Washington',
            qualifications='BSc Computer Science',
            skills='Python, Django, Flutter'
        )

        # Candidate 2 (Bob)
        self.other_candidate_user = User.objects.create_user(
            email='bob@example.com',
            username='bob',
            password='CandidatePassword123!',
            role=User.Role.CANDIDATE
        )
        self.other_candidate_profile = CandidateProfile.objects.create(
            user=self.other_candidate_user,
            full_name='Bob Jones'
        )

        # Company & Vacancy for application testing
        self.company_user = User.objects.create_user(
            email='hr@innovate.com',
            username='innovate',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Innovate AI',
            phone='1234567890',
            address='Tech Hub 1',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )
        self.vacancy = Vacancy.objects.create(
            company=self.company,
            position='AI Engineer',
            description='Build AI models.',
            application_deadline='2026-12-31'
        )
        self.application = Application.objects.create(
            vacancy=self.vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.PENDING
        )

    # 1. Candidate Dashboard
    def test_candidate_dashboard_stats(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/v1/candidates/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['candidate']['full_name'], 'Alice Smith')
        self.assertEqual(data['applications']['total_applied'], 1)
        self.assertEqual(data['applications']['pending'], 1)
        self.assertGreater(data['candidate']['profile_completeness_percentage'], 0)

    # 2. Candidate Profile View and Update
    def test_candidate_profile_view_and_update(self):
        self.client.force_authenticate(user=self.candidate_user)
        # View
        response = self.client.get('/api/v1/candidates/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Alice Smith')
        self.assertEqual(response.data['city'], 'Seattle')

        # Update
        response = self.client.put('/api/v1/candidates/profile/', {
            'full_name': 'Alice M. Smith',
            'city': 'San Francisco',
            'state': 'California',
            'skills': 'Python, Django, Flutter, PyTorch'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_profile.refresh_from_db()
        self.assertEqual(self.candidate_profile.full_name, 'Alice M. Smith')
        self.assertEqual(self.candidate_profile.city, 'San Francisco')

    # 3. Photo Upload & Validation
    def test_candidate_photo_upload_valid(self):
        self.client.force_authenticate(user=self.candidate_user)
        # 1x1 GIF / PNG image bytes
        image_bytes = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image_file = SimpleUploadedFile("avatar.jpg", image_bytes, content_type="image/jpeg")

        response = self.client.post('/api/v1/candidates/profile/photo/', {'photo': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_profile.refresh_from_db()
        self.assertTrue(bool(self.candidate_profile.photo))

    def test_candidate_photo_upload_invalid_type(self):
        self.client.force_authenticate(user=self.candidate_user)
        bad_file = SimpleUploadedFile("malicious.exe", b'executable content', content_type="application/octet-stream")
        response = self.client.post('/api/v1/candidates/profile/photo/', {'photo': bad_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 4. Resume Upload & Delete
    def test_candidate_resume_upload_and_delete(self):
        self.client.force_authenticate(user=self.candidate_user)
        resume_file = SimpleUploadedFile("resume.pdf", b'%PDF-1.4 sample pdf content', content_type="application/pdf")
        response = self.client.post('/api/v1/candidates/profile/resume/', {'resume': resume_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_profile.refresh_from_db()
        self.assertTrue(bool(self.candidate_profile.resume))

        # Delete resume
        del_response = self.client.delete('/api/v1/candidates/profile/resume/')
        self.assertEqual(del_response.status_code, status.HTTP_200_OK)
        self.candidate_profile.refresh_from_db()
        self.assertFalse(bool(self.candidate_profile.resume))

    # 5. Legacy Flutter Registration Endpoint (/myapp/user_registration/)
    def test_legacy_user_registration(self):
        response = self.client.post('/myapp/user_registration/', {
            'name': 'Charlie Brown',
            'email': 'charlie@example.com',
            'password': 'CharliePassword123!',
            'cpassword': 'CharliePassword123!',
            'place': 'Green Valley',
            'dob': '1995-10-25',
            'phone': '1234567890',
            'city': 'Portland',
            'state': 'Oregon',
            'post': 'North',
            'pin': '97201',
            'gender': 'Male'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Registration successful')
        new_user = User.objects.get(email='charlie@example.com')
        self.assertEqual(new_user.candidate_profile.full_name, 'Charlie Brown')

    # 6. Legacy Flutter Profile View Endpoint (/myapp/user_profile/)
    def test_legacy_user_profile(self):
        response = self.client.post('/myapp/user_profile/', {
            'lid': str(self.candidate_user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['name'], 'Alice Smith')
        self.assertEqual(data['email'], 'alice@example.com')
        self.assertEqual(data['city'], 'Seattle')

    # 7. Legacy Flutter Profile Edit Pre-fill (/myapp/user_profileviewforedit/)
    def test_legacy_user_profileviewforedit(self):
        response = self.client.post('/myapp/user_profileviewforedit/', {
            'lid': str(self.candidate_user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['name'], 'Alice Smith')
        self.assertIn('gender', data)

    # 8. Legacy Flutter Profile Update Endpoint (/myapp/user_edit_profile/)
    def test_legacy_user_edit_profile(self):
        response = self.client.post('/myapp/user_edit_profile/', {
            'lid': str(self.candidate_user.id),
            'name': 'Alice Allison Smith',
            'email': 'alice.smith@example.com',
            'phone': '9998887776',
            'city': 'Bellevue',
            'state': 'Washington',
            'place': 'Downtown',
            'post': 'Central',
            'pin': '98004',
            'gender': 'Female',
            'dob': '1998-05-15'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.candidate_profile.refresh_from_db()
        self.candidate_user.refresh_from_db()
        self.assertEqual(self.candidate_profile.full_name, 'Alice Allison Smith')
        self.assertEqual(self.candidate_user.email, 'alice.smith@example.com')
        self.assertEqual(self.candidate_profile.city, 'Bellevue')
