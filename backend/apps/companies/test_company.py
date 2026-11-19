from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient

from apps.companies.models import CompanyProfile, CompanyReview
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application

User = get_user_model()


class CompanyModulePhase5Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Approved Company
        self.approved_company_user = User.objects.create_user(
            email='hr@technova.com',
            username='technova_co',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.approved_company = CompanyProfile.objects.create(
            user=self.approved_company_user,
            company_name='TechNova Solutions',
            phone='+1-555-1234',
            address='742 Evergreen Terrace',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 2. Pending Company
        self.pending_company_user = User.objects.create_user(
            email='hr@pending.com',
            username='pending_co',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.pending_company = CompanyProfile.objects.create(
            user=self.pending_company_user,
            company_name='Pending Labs',
            phone='+1-555-9999',
            address='101 Main St',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )

        # 3. Other Company
        self.other_company_user = User.objects.create_user(
            email='hr@other.com',
            username='other_co',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.other_company = CompanyProfile.objects.create(
            user=self.other_company_user,
            company_name='Other Industries',
            phone='+1-555-4321',
            address='500 Commerce Ave',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 4. Candidate
        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',
            username='alice_c',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Alice Smith',
            skills='Python, Django, Flutter'
        )

        # 5. Vacancy for approved company
        self.vacancy = Vacancy.objects.create(
            company=self.approved_company,
            position='Full Stack Django/Flutter Engineer',
            description='Build next-gen interview platforms.',
            no_of_vacancy=3,
            application_deadline=timezone.now().date() + timedelta(days=20)
        )

        # 6. Application
        self.application = Application.objects.create(
            vacancy=self.vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.PENDING
        )

    # 1. Company Dashboard
    def test_company_dashboard_stats(self):
        self.client.force_authenticate(user=self.approved_company_user)
        response = self.client.get('/api/v1/companies/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['company']['name'], 'TechNova Solutions')
        self.assertTrue(data['company']['is_verified'])
        self.assertEqual(data['vacancies']['total'], 1)
        self.assertEqual(data['applications']['total'], 1)

    # 2. Company Profile View and Update
    def test_company_profile_view_and_update(self):
        self.client.force_authenticate(user=self.approved_company_user)
        # View
        response = self.client.get('/api/v1/companies/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'TechNova Solutions')

        # Update
        response = self.client.put('/api/v1/companies/profile/', {
            'company_name': 'TechNova Global Inc.',
            'website': 'https://technovaglobal.io',
            'description': 'Leading AI interview technology.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approved_company.refresh_from_db()
        self.assertEqual(self.approved_company.company_name, 'TechNova Global Inc.')
        self.assertEqual(self.approved_company.website, 'https://technovaglobal.io')

    # 3. Vacancy Creation: Verified vs Pending
    def test_verified_company_can_post_vacancy(self):
        self.client.force_authenticate(user=self.approved_company_user)
        payload = {
            'position': 'AI Prompt Engineer',
            'description': 'Develop cutting-edge prompt engineering solutions.',
            'no_of_vacancy': 2,
            'application_deadline': (timezone.now().date() + timedelta(days=15)).isoformat()
        }
        response = self.client.post('/api/v1/companies/vacancies/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['vacancy']['position'], 'AI Prompt Engineer')

    def test_pending_company_cannot_post_vacancy(self):
        self.client.force_authenticate(user=self.pending_company_user)
        payload = {
            'position': 'Marketing Specialist',
            'description': 'Grow business awareness.',
            'application_deadline': (timezone.now().date() + timedelta(days=10)).isoformat()
        }
        response = self.client.post('/api/v1/companies/vacancies/', payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only approved and verified companies can publish', response.data['message'])

    # 4. Vacancy Detail, Update, and Delete
    def test_vacancy_update_and_delete(self):
        self.client.force_authenticate(user=self.approved_company_user)
        # Update
        response = self.client.put(f'/api/v1/companies/vacancies/{self.vacancy.id}/', {
            'position': 'Lead Django/Flutter Engineer',
            'description': 'Updated description',
            'application_deadline': self.vacancy.application_deadline.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vacancy.refresh_from_db()
        self.assertEqual(self.vacancy.position, 'Lead Django/Flutter Engineer')

        # Delete
        del_response = self.client.delete(f'/api/v1/companies/vacancies/{self.vacancy.id}/')
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vacancy.objects.filter(id=self.vacancy.id).exists())

    def test_cannot_access_other_company_vacancy(self):
        self.client.force_authenticate(user=self.other_company_user)
        response = self.client.get(f'/api/v1/companies/vacancies/{self.vacancy.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 5. Application Management
    def test_company_view_vacancy_applications(self):
        self.client.force_authenticate(user=self.approved_company_user)
        response = self.client.get(f'/api/v1/companies/vacancies/{self.vacancy.id}/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['candidate']['full_name'], 'Alice Smith')

    def test_company_shortlist_application(self):
        self.client.force_authenticate(user=self.approved_company_user)
        response = self.client.post(f'/api/v1/companies/applications/{self.application.id}/status/', {
            'status': 'SHORTLISTED',
            'company_notes': 'Strong background in Django and Flutter.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'SHORTLISTED')
        self.assertEqual(self.application.company_notes, 'Strong background in Django and Flutter.')

    def test_company_reject_application(self):
        self.client.force_authenticate(user=self.approved_company_user)
        response = self.client.post(f'/api/v1/companies/applications/{self.application.id}/status/', {
            'status': 'REJECTED',
            'company_notes': 'Position closed.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'REJECTED')

    # 6. Company Reviews
    def test_company_reviews_list(self):
        CompanyReview.objects.create(
            company=self.approved_company,
            candidate=self.candidate_profile,
            rating=4.5,
            review='Excellent recruitment process.'
        )
        self.client.force_authenticate(user=self.approved_company_user)
        response = self.client.get('/api/v1/companies/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(float(response.data['results'][0]['rating']), 4.5)

    # 7. Legacy Flutter Endpoints
    def test_legacy_company_dropdown(self):
        response = self.client.post('/myapp/companytocomplaint/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertGreaterEqual(len(data['data']), 3)
        # Check structure has 'id' and 'name'
        self.assertIn('id', data['data'][0])
        self.assertIn('name', data['data'][0])

    def test_legacy_review_company(self):
        response = self.client.post('/myapp/review_company/', {
            'lid': str(self.candidate_user.id),
            'Company_id': str(self.approved_company.id),
            'rating': '5.0',
            'review': 'Great company culture and fast interview response.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Review submitted successfully!')
        # Check database
        review = CompanyReview.objects.get(
            company=self.approved_company,
            candidate=self.candidate_profile
        )
        self.assertEqual(float(review.rating), 5.0)
        self.assertEqual(review.review, 'Great company culture and fast interview response.')
