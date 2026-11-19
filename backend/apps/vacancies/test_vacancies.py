from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application

User = get_user_model()


class VacancyAndApplicationPhase7Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Approved Company
        self.company_user = User.objects.create_user(
            email='hr@quantum.com',
            username='quantum_ai',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Quantum Systems',
            phone='1234567890',
            address='Silicon Valley',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 2. Unapproved (Pending) Company
        self.pending_company_user = User.objects.create_user(
            email='hr@stealth.com',
            username='stealth_ai',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.pending_company = CompanyProfile.objects.create(
            user=self.pending_company_user,
            company_name='Stealth AI',
            phone='0987654321',
            address='Hidden Valley',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )

        # 3. Candidate
        self.candidate_user = User.objects.create_user(
            email='david@example.com',
            username='david',
            password='CandidatePassword123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='David Miller',
            skills='Python, Django, React'
        )

        # 4. Vacancies
        # Active vacancy (approved company, future deadline)
        self.active_vacancy = Vacancy.objects.create(
            company=self.company,
            position='Senior Python Engineer',
            description='Design scalable APIs with Django.',
            required_skills='Python, Django, PostgreSQL',
            location='San Francisco, CA',
            no_of_vacancy=2,
            application_deadline=timezone.now().date() + timedelta(days=25),
            status=Vacancy.Status.ACTIVE
        )

        # Expired vacancy
        self.expired_vacancy = Vacancy.objects.create(
            company=self.company,
            position='Junior QA Tester',
            description='Manual and automated testing.',
            application_deadline=timezone.now().date() - timedelta(days=5),
            status=Vacancy.Status.ACTIVE
        )

        # Vacancy from unapproved company
        self.unapproved_vacancy = Vacancy.objects.create(
            company=self.pending_company,
            position='Stealth Researcher',
            description='Secret AI research.',
            application_deadline=timezone.now().date() + timedelta(days=30),
            status=Vacancy.Status.ACTIVE
        )

    # 1. Public Vacancy List & Filters
    def test_public_vacancy_list_filters_closed_and_unapproved(self):
        response = self.client.get('/api/v1/vacancies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active_vacancy should appear
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['position'], 'Senior Python Engineer')

    def test_public_vacancy_search(self):
        response = self.client.get('/api/v1/vacancies/?search=PostgreSQL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_public_vacancy_detail(self):
        response = self.client.get(f'/api/v1/vacancies/{self.active_vacancy.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['position'], 'Senior Python Engineer')
        self.assertEqual(response.data['company']['company_name'], 'Quantum Systems')

    # 2. Candidate Job Application & Duplicate Prevention
    def test_candidate_apply_vacancy_success(self):
        self.client.force_authenticate(user=self.candidate_user)
        resume_file = SimpleUploadedFile("david_cv.pdf", b'%PDF-1.4 sample content', content_type="application/pdf")
        response = self.client.post(f'/api/v1/vacancies/{self.active_vacancy.id}/apply/', {
            'resume': resume_file,
            'cover_letter': 'I am very excited to join Quantum Systems.'
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')
        # Check DB
        app = Application.objects.get(vacancy=self.active_vacancy, candidate=self.candidate_profile)
        self.assertEqual(app.status, Application.Status.PENDING)
        self.assertEqual(app.cover_letter, 'I am very excited to join Quantum Systems.')

    def test_candidate_apply_duplicate_rejected(self):
        self.client.force_authenticate(user=self.candidate_user)
        # Apply once
        self.client.post(f'/api/v1/vacancies/{self.active_vacancy.id}/apply/', {})
        # Apply twice (duplicate)
        response = self.client.post(f'/api/v1/vacancies/{self.active_vacancy.id}/apply/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already applied', response.data['error'])

    def test_candidate_cannot_apply_for_expired_vacancy(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.post(f'/api/v1/vacancies/{self.expired_vacancy.id}/apply/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 3. Application Tracking & Withdrawal
    def test_candidate_my_applications_list(self):
        Application.objects.create(
            vacancy=self.active_vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.SHORTLISTED
        )
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/v1/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], 'SHORTLISTED')

    def test_candidate_withdraw_pending_application(self):
        app = Application.objects.create(
            vacancy=self.active_vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.PENDING
        )
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.post(f'/api/v1/applications/{app.id}/withdraw/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Application.objects.filter(id=app.id).exists())

    # 4. Flutter Legacy Endpoints
    def test_legacy_user_view_vacancy(self):
        response = self.client.post('/myapp/user_view_vacancy/', {
            'lid': str(self.candidate_user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(len(data['data']), 1)
        item = data['data'][0]
        self.assertEqual(item['position'], 'Senior Python Engineer')
        self.assertEqual(item['COMPANY'], 'Quantum Systems')
        self.assertIn('no_of_vaccancy', item)

    def test_legacy_user_apply_vacancy_success_and_duplicate(self):
        # 1. Apply successfully
        resume = SimpleUploadedFile("cv.pdf", b'%PDF content', content_type="application/pdf")
        response = self.client.post('/myapp/user_apply_vacancy/', {
            'lid': str(self.candidate_user.id),
            'vacancy_id': str(self.active_vacancy.id),
            'resume': resume
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Applied successfully')

        # 2. Duplicate attempt
        dup_response = self.client.post('/myapp/user_apply_vacancy/', {
            'lid': str(self.candidate_user.id),
            'vacancy_id': str(self.active_vacancy.id),
        })
        self.assertEqual(dup_response.status_code, status.HTTP_200_OK)
        dup_data = dup_response.json()
        self.assertEqual(dup_data['status'], 'no')
        self.assertIn('already applied', dup_data['message'])

    def test_legacy_view_applied_vacancy(self):
        Application.objects.create(
            vacancy=self.active_vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.ACCEPTED
        )
        response = self.client.post('/myapp/view_applied_vacancy/', {
            'lid': str(self.candidate_user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(len(data['data']), 1)
        item = data['data'][0]
        self.assertEqual(item['VACCANCY'], 'Senior Python Engineer')
        self.assertEqual(item['company'], 'Quantum Systems')
        self.assertEqual(item['status'], 'Accepted')
