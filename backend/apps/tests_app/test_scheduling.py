import datetime
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from apps.tests_app.models import TestSchedule, TestCandidateAssignment
from apps.interviews.models import InterviewSchedule

User = get_user_model()


class TestAndInterviewSchedulingTests(APITestCase):
    def setUp(self):
        # 1. Company User & Profile (Verified)
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
            address='Tech Park, Suite 400',
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        )

        # 2. Unverified Company User & Profile
        self.unverified_user = User.objects.create_user(
            username='pendingcorp',
            email='hr@pendingcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )
        self.unverified_profile = CompanyProfile.objects.create(
            user=self.unverified_user,
            company_name='Pending Startup',
            email='hr@pendingcorp.com',
            phone='9876543211',
            address='Incubator Hub',
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )

        # 3. Candidate User & Profile
        self.candidate_user = User.objects.create_user(
            username='alice_dev',
            email='alice@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name='Alice Developer',
            phone='9123456789',
            city='Bengaluru',
            state='Karnataka'
        )

        # 4. Vacancy and Application
        self.vacancy = Vacancy.objects.create(
            company=self.company_profile,
            position='Backend Developer',
            description='Build robust Python/Django APIs.',
            required_qualifications='B.Tech / MCA in CS',
            required_skills='Python, Django, PostgreSQL',
            experience_years=3,
            location='Bengaluru, India',
            no_of_vacancy=2,
            application_deadline=timezone.localdate() + datetime.timedelta(days=30),
            status=Vacancy.Status.ACTIVE
        )

        self.application = Application.objects.create(
            vacancy=self.vacancy,
            candidate=self.candidate_profile,
            status=Application.Status.SHORTLISTED
        )

        # Base test date in the future
        self.schedule_date = timezone.localdate() + datetime.timedelta(days=5)

    def test_company_can_schedule_test(self):
        """Verified company schedules a test successfully."""
        self.client.force_authenticate(user=self.company_user)
        payload = {
            'test_name': 'Django & Algorithms Assessment',
            'test_type': 'TECHNICAL',
            'date': str(self.schedule_date),
            'start_time': '10:00:00',
            'end_time': '11:30:00',
            'duration_minutes': 90,
            'max_score': 100,
            'instructions': 'Complete all 3 questions within 90 mins.'
        }
        response = self.client.post('/api/v1/tests/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['test']['test_name'], 'Django & Algorithms Assessment')

    def test_unverified_company_cannot_schedule_test(self):
        """Unverified company is blocked from scheduling tests."""
        self.client.force_authenticate(user=self.unverified_user)
        payload = {
            'test_name': 'Pending Assessment',
            'test_type': 'TECHNICAL',
            'date': str(self.schedule_date),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60
        }
        response = self.client.post('/api/v1/tests/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_candidates_and_record_attendance(self):
        """Company assigns candidate to test and records attendance/score."""
        test = TestSchedule.objects.create(
            company=self.company_profile,
            test_name='Python Core MCQ',
            test_type='MCQ',
            date=self.schedule_date,
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            duration_minutes=60
        )

        self.client.force_authenticate(user=self.company_user)
        assign_response = self.client.post(
            f'/api/v1/tests/{test.id}/assign-candidates/',
            {'candidate_ids': [self.candidate_profile.id]},
            format='json'
        )
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertEqual(assign_response.data['total_assigned'], 1)

        # Record Attendance & Score
        attend_response = self.client.post(
            f'/api/v1/tests/{test.id}/attendance/',
            {
                'candidate_id': self.candidate_profile.id,
                'attendance_status': 'ATTENDED',
                'score': 88.5,
                'remarks': 'Excellent algorithm comprehension.'
            },
            format='json'
        )
        self.assertEqual(attend_response.status_code, status.HTTP_200_OK)
        self.assertEqual(attend_response.data['score'], 88.5)

    def test_candidate_can_view_assigned_tests(self):
        """Candidate views scheduled tests assigned to them."""
        test = TestSchedule.objects.create(
            company=self.company_profile,
            test_name='System Architecture Exam',
            test_type='TECHNICAL',
            date=self.schedule_date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
            duration_minutes=90
        )
        TestCandidateAssignment.objects.create(
            test=test,
            candidate=self.candidate_profile
        )

        self.client.force_authenticate(user=self.candidate_user)
        response = self.client.get('/api/v1/tests/my-tests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['test_name'], 'System Architecture Exam')

    def test_company_can_schedule_interview(self):
        """Company schedules an interview with candidate."""
        self.client.force_authenticate(user=self.company_user)
        payload = {
            'candidate_id': self.candidate_profile.id,
            'application_id': self.application.id,
            'interview_title': 'Technical Round 1: System Design',
            'interview_type': 'TECHNICAL',
            'date': str(self.schedule_date),
            'start_time': '16:00:00',
            'end_time': '17:00:00',
            'meeting_link': 'https://meet.google.com/abc-defg-hij',
            'notes': 'Candidate should prepare a distributed caching design.'
        }
        response = self.client.post('/api/v1/interviews/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['interview']['interview_title'], 'Technical Round 1: System Design')

    def test_interview_conflict_detection(self):
        """Scheduling overlapping interview on same date/time returns conflict error."""
        # Create an existing interview from 14:00 to 15:00
        InterviewSchedule.objects.create(
            company=self.company_profile,
            candidate=self.candidate_profile,
            interview_title='Existing HR Round',
            interview_type='HR',
            date=self.schedule_date,
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            status=InterviewSchedule.Status.SCHEDULED
        )

        self.client.force_authenticate(user=self.company_user)
        # Attempt to schedule overlapping interview (14:30 to 15:30)
        payload = {
            'candidate_id': self.candidate_profile.id,
            'interview_title': 'Overlapping Tech Round',
            'interview_type': 'TECHNICAL',
            'date': str(self.schedule_date),
            'start_time': '14:30:00',
            'end_time': '15:30:00'
        }
        response = self.client.post('/api/v1/interviews/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduling_conflict', response.data)

    def test_reschedule_and_cancel_interview(self):
        """Company can reschedule and cancel interview with reason."""
        interview = InterviewSchedule.objects.create(
            company=self.company_profile,
            candidate=self.candidate_profile,
            interview_title='Preliminary Interview',
            interview_type='TECHNICAL',
            date=self.schedule_date,
            start_time=datetime.time(11, 0),
            end_time=datetime.time(12, 0),
            status=InterviewSchedule.Status.SCHEDULED
        )

        self.client.force_authenticate(user=self.company_user)

        # Reschedule
        new_date = self.schedule_date + datetime.timedelta(days=2)
        resched_resp = self.client.post(
            f'/api/v1/interviews/{interview.id}/reschedule/',
            {
                'date': str(new_date),
                'start_time': '13:00:00',
                'end_time': '14:00:00',
                'notes': 'Rescheduled due to interviewer availability.'
            },
            format='json'
        )
        self.assertEqual(resched_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resched_resp.data['interview']['status'], 'RESCHEDULED')

        # Cancel
        cancel_resp = self.client.post(
            f'/api/v1/interviews/{interview.id}/cancel/',
            {'cancellation_reason': 'Position filled internally.'},
            format='json'
        )
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_resp.data['status'], 'ok')

        interview.refresh_from_db()
        self.assertEqual(interview.status, InterviewSchedule.Status.CANCELLED)

    def test_legacy_flutter_user_view_test_endpoint(self):
        """Matches Flutter test_details.dart: POST /myapp/user_view_test/"""
        test = TestSchedule.objects.create(
            company=self.company_profile,
            test_name='Aptitude Assessment',
            test_type='APTITUDE',
            date=self.schedule_date,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            status='SCHEDULED'
        )
        TestCandidateAssignment.objects.create(
            test=test,
            candidate=self.candidate_profile
        )

        # Request using Application ID (as passed by Flutter view_applied_vacancy)
        response = self.client.post(
            '/myapp/user_view_test/',
            {'candidate_id': str(self.application.id)},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertTrue(len(response.data['data']) >= 1)

        first_test = response.data['data'][0]
        self.assertEqual(first_test['test_name'], 'Aptitude Assessment')
        self.assertEqual(first_test['test_type'], 'APTITUDE')
        self.assertEqual(first_test['date'], str(self.schedule_date))
        self.assertIn('10:00 AM', first_test['start'])
        self.assertIn('11:00 AM', first_test['end'])
        self.assertEqual(first_test['status'], 'Scheduled')
