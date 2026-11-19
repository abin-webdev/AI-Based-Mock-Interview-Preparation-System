from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile

User = get_user_model()


class AuthenticationPhase3Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Admin User
        self.admin_user = User.objects.create_superuser(
            email='admin@interviews.org',
            username='systemadmin',
            password='AdminPassword123!',
            role=User.Role.ADMIN
        )

        # Create Verified Company User
        self.company_user = User.objects.create_user(
            email='hr@technova.com',
            username='technovacorp',
            password='CompanyPassword123!',
            role=User.Role.COMPANY
        )
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='TechNova Corp',
            email='hr@technova.com',
            phone='+1234567890',
            address='123 Tech Park',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # Create Candidate User
        self.candidate_user = User.objects.create_user(
            email='jane@example.com',
            username='janedoe',
            password='CandidatePassword123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Jane Doe',
            phone='+919876543210',
            city='Ernakulam',
            state='Kerala'
        )

    # 1. Candidate Registration API
    def test_candidate_registration_success(self):
        payload = {
            'email': 'newcandidate@example.com',
            'username': 'newcandidate',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'full_name': 'New Candidate',
            'phone': '9876543211',
            'city': 'Kochi',
            'state': 'Kerala'
        }
        response = self.client.post('/api/v1/auth/register/candidate/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')
        self.assertIn('tokens', response.data)
        user = User.objects.get(email='newcandidate@example.com')
        self.assertEqual(user.role, User.Role.CANDIDATE)
        self.assertEqual(user.candidate_profile.full_name, 'New Candidate')

    def test_candidate_registration_password_mismatch(self):
        payload = {
            'email': 'mismatch@example.com',
            'username': 'mismatch',
            'password': 'SecurePassword123!',
            'confirm_password': 'DifferentPassword123!',
            'full_name': 'Mismatch Test'
        }
        response = self.client.post('/api/v1/auth/register/candidate/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_candidate_registration_duplicate_email(self):
        payload = {
            'email': 'jane@example.com',
            'username': 'jane2',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'full_name': 'Duplicate Email'
        }
        response = self.client.post('/api/v1/auth/register/candidate/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 2. Company Registration API
    def test_company_registration_defaults_to_pending(self):
        payload = {
            'email': 'contact@startup.io',
            'username': 'startupio',
            'password': 'CompanyPassword123!',
            'confirm_password': 'CompanyPassword123!',
            'company_name': 'Startup AI Labs',
            'phone': '9898989898',
            'address': 'Silicon Tower 4B',
            'website': 'https://startup.io'
        }
        response = self.client.post('/api/v1/auth/register/company/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='contact@startup.io')
        self.assertEqual(user.role, User.Role.COMPANY)
        self.assertEqual(user.company_profile.verification_status, CompanyProfile.VerificationStatus.PENDING)
        self.assertFalse(user.company_profile.is_verified)

    # 3. JWT Token Authentication
    def test_jwt_login_with_email(self):
        response = self.client.post('/api/v1/auth/token/', {
            'username': 'jane@example.com',
            'password': 'CandidatePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'CANDIDATE')

    def test_jwt_login_invalid_password(self):
        response = self.client.post('/api/v1/auth/token/', {
            'username': 'jane@example.com',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 4. Current User & Role Details
    def test_current_user_me_endpoint(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'jane@example.com')
        self.assertEqual(response.data['candidate_details']['full_name'], 'Jane Doe')

    # 5. Password Change API
    def test_change_password(self):
        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.post('/api/v1/auth/change-password/', {
            'old_password': 'CandidatePassword123!',
            'new_password': 'BrandNewPassword123!',
            'confirm_password': 'BrandNewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate_user.refresh_from_db()
        self.assertTrue(self.candidate_user.check_password('BrandNewPassword123!'))

    # 6. Legacy Flutter Login Endpoint (/myapp/User_login/)
    def test_legacy_flutter_login_candidate_success(self):
        response = self.client.post('/myapp/User_login/', {
            'Username': 'jane@example.com',
            'Password': 'CandidatePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['type'], 'user')
        self.assertEqual(data['lid'], str(self.candidate_user.id))

    def test_legacy_flutter_login_company_approved_success(self):
        response = self.client.post('/myapp/User_login/', {
            'Username': 'hr@technova.com',
            'Password': 'CompanyPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['type'], 'company')
        self.assertEqual(data['lid'], str(self.company_user.id))

    def test_legacy_flutter_login_company_pending_restricted(self):
        # Create pending company
        pending_user = User.objects.create_user(
            email='pending@company.com',
            username='pendingcomp',
            password='Password123!',
            role=User.Role.COMPANY
        )
        CompanyProfile.objects.create(
            user=pending_user,
            company_name='Pending Co',
            phone='123456',
            address='Street 1',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )
        response = self.client.post('/myapp/User_login/', {
            'Username': 'pending@company.com',
            'Password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'no')
        self.assertIn('PENDING', data['message'])

    def test_legacy_flutter_login_invalid_credentials(self):
        response = self.client.post('/myapp/User_login/', {
            'Username': 'jane@example.com',
            'Password': 'IncorrectPassword'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'no')
        self.assertIn('Invalid', data['message'])
