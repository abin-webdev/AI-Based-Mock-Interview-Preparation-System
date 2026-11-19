from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile
from apps.ai_interviews.models import AIMockSession, AIMockQuestion, AIMockAnswer

User = get_user_model()


class AIMockInterviewTests(APITestCase):
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

        # 2. Candidate 2 (Bob)
        self.user_bob = User.objects.create_user(
            username='bob_engineer',
            email='bob@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        self.candidate_bob = CandidateProfile.objects.create(
            user=self.user_bob,
            full_name='Bob Engineer',
            phone='9123456780',
            city='Mumbai',
            state='Maharashtra'
        )

        # 3. Company User
        self.company_user = User.objects.create_user(
            username='techcorp',
            email='hr@techcorp.com',
            password='Password123!',
            role=User.Role.COMPANY
        )

    def test_candidate_can_create_mock_session_with_generated_questions(self):
        """Candidate creates session; questions are dynamically generated and populated."""
        self.client.force_authenticate(user=self.user_alice)
        payload = {
            'job_role': 'Python Django Backend Engineer',
            'category': 'TECHNICAL',
            'difficulty': 'MID',
            'question_count': 5,
            'duration_minutes': 20,
            'camera_consent_given': True
        }
        response = self.client.post('/api/v1/ai-interviews/sessions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'ok')

        session_data = response.data['session']
        self.assertEqual(session_data['job_role'], 'Python Django Backend Engineer')
        self.assertEqual(session_data['status'], 'CREATED')
        self.assertEqual(len(session_data['questions']), 5)

        # Check that questions have realistic rubrics and expected keywords
        first_q = session_data['questions'][0]
        self.assertEqual(first_q['question_number'], 1)
        self.assertTrue(len(first_q['question_text']) > 15)
        self.assertTrue(len(first_q['expected_keywords']) > 5)
        self.assertTrue(len(first_q['evaluation_rubric']) > 15)

    def test_generate_hr_questions(self):
        """Candidate requests HR category interview; receives tailored HR questions."""
        self.client.force_authenticate(user=self.user_alice)
        payload = {
            'job_role': 'Software Engineer',
            'category': 'HR',
            'difficulty': 'JUNIOR',
            'question_count': 3,
            'duration_minutes': 15
        }
        response = self.client.post('/api/v1/ai-interviews/sessions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        questions = response.data['session']['questions']
        self.assertEqual(len(questions), 3)
        for q in questions:
            self.assertEqual(q['category'], 'HR')

    def test_company_cannot_create_mock_session(self):
        """Company users cannot create mock interview sessions."""
        self.client.force_authenticate(user=self.company_user)
        payload = {
            'job_role': 'Software Engineer',
            'category': 'TECHNICAL',
            'difficulty': 'MID',
            'question_count': 3
        }
        response = self.client.post('/api/v1/ai-interviews/sessions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_lifecycle_and_answer_submission(self):
        """Test complete session progression: create -> start -> answer -> update answer."""
        self.client.force_authenticate(user=self.user_alice)

        # 1. Create session
        create_resp = self.client.post('/api/v1/ai-interviews/sessions/', {
            'job_role': 'Flutter Mobile Developer',
            'category': 'TECHNICAL',
            'difficulty': 'MID',
            'question_count': 3
        }, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        session_id = create_resp.data['session']['id']
        questions = create_resp.data['session']['questions']
        q1_id = questions[0]['id']

        # 2. Start session
        start_resp = self.client.post(f'/api/v1/ai-interviews/sessions/{session_id}/start/')
        self.assertEqual(start_resp.status_code, status.HTTP_200_OK)

        session = AIMockSession.objects.get(id=session_id)
        self.assertEqual(session.status, AIMockSession.Status.IN_PROGRESS)
        self.assertIsNotNone(session.started_at)

        # 3. Submit Answer for Question 1
        answer_payload = {
            'question_id': q1_id,
            'answer_text': 'Flutter uses a reactive framework where the Widget tree represents immutable UI configuration, while RenderObjects handle layout and painting.',
            'time_taken_seconds': 45
        }
        ans_resp = self.client.post(
            f'/api/v1/ai-interviews/sessions/{session_id}/submit-answer/',
            answer_payload,
            format='json'
        )
        self.assertEqual(ans_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ans_resp.data['total_answered'], 1)

        # 4. Verify question now reflects has_answer = True
        detail_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{session_id}/')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        q1_data = detail_resp.data['questions'][0]
        self.assertTrue(q1_data['has_answer'])
        self.assertEqual(q1_data['answer']['time_taken_seconds'], 45)

        # 5. Candidate updates their answer
        updated_payload = {
            'question_id': q1_id,
            'answer_text': 'Updated answer: In Flutter, widgets are rebuilt efficiently using the Element tree diffing algorithm to ensure 60fps performance.',
            'time_taken_seconds': 60
        }
        update_resp = self.client.post(
            f'/api/v1/ai-interviews/sessions/{session_id}/submit-answer/',
            updated_payload,
            format='json'
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertIn('Updated answer', update_resp.data['answer']['answer_text'])

    def test_candidate_cannot_access_other_candidates_session(self):
        """Strict candidate isolation: Bob cannot view or submit answers to Alice's session."""
        # Alice creates session
        self.client.force_authenticate(user=self.user_alice)
        create_resp = self.client.post('/api/v1/ai-interviews/sessions/', {
            'job_role': 'DevOps Engineer',
            'category': 'TECHNICAL',
            'difficulty': 'SENIOR',
            'question_count': 2
        }, format='json')
        alice_session_id = create_resp.data['session']['id']
        alice_q_id = create_resp.data['session']['questions'][0]['id']

        # Bob logs in
        self.client.force_authenticate(user=self.user_bob)

        # Bob attempts to view Alice's session
        get_resp = self.client.get(f'/api/v1/ai-interviews/sessions/{alice_session_id}/')
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Bob attempts to submit answer to Alice's session
        submit_resp = self.client.post(
            f'/api/v1/ai-interviews/sessions/{alice_session_id}/submit-answer/',
            {'question_id': alice_q_id, 'answer_text': 'Unauthorized attempt'},
            format='json'
        )
        self.assertEqual(submit_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_abandon_mock_session(self):
        """Candidate can abandon an active mock session."""
        self.client.force_authenticate(user=self.user_alice)
        create_resp = self.client.post('/api/v1/ai-interviews/sessions/', {
            'job_role': 'QA Engineer',
            'category': 'GENERAL',
            'difficulty': 'JUNIOR',
            'question_count': 2
        }, format='json')
        session_id = create_resp.data['session']['id']

        abandon_resp = self.client.post(f'/api/v1/ai-interviews/sessions/{session_id}/abandon/')
        self.assertEqual(abandon_resp.status_code, status.HTTP_200_OK)

        session = AIMockSession.objects.get(id=session_id)
        self.assertEqual(session.status, AIMockSession.Status.ABANDONED)
