import sys
import time
import uuid
import requests

BASE_URL = 'https://ai-mock-interview-backend-nklz.onrender.com'
RUN_ID = str(uuid.uuid4())[:8]

results = []
client = requests.Session()

def record(endpoint, method, status_code, expected_status, passed, expected_resp, actual_resp, notes=""):
    results.append({
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'expected_status': expected_status,
        'passed': passed,
        'expected_resp': str(expected_resp)[:300],
        'actual_resp': str(actual_resp)[:300],
        'notes': notes
    })
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {method} {endpoint} -> {status_code} (Expected {expected_status})")
    if not passed:
        print(f"   Actual: {str(actual_resp)[:200]}")

print(f"=== Starting Production API Verification against {BASE_URL} (Run {RUN_ID}) ===")

# 1. Health Check
try:
    r = client.get(f"{BASE_URL}/api/health/")
    record('/api/health/', 'GET', r.status_code, 200, r.status_code == 200, '{"status": "healthy"}', r.text)
except Exception as e:
    record('/api/health/', 'GET', 0, 200, False, '200 OK', str(e))

# 2. OpenAPI / Swagger Documentation
try:
    r = client.get(f"{BASE_URL}/api/docs/")
    record('/api/docs/', 'GET', r.status_code, 200, r.status_code == 200, 'HTML Swagger UI', f"Length: {len(r.text)}")
except Exception as e:
    record('/api/docs/', 'GET', 0, 200, False, '200 OK', str(e))

try:
    r = client.get(f"{BASE_URL}/api/schema/")
    record('/api/schema/', 'GET', r.status_code, 200, r.status_code == 200, 'OpenAPI 3.0 schema YAML/JSON', f"Length: {len(r.text)}")
except Exception as e:
    record('/api/schema/', 'GET', 0, 200, False, '200 OK', str(e))

# 3. CORS Preflight Check
try:
    headers = {
        'Origin': 'https://flutter-mock-interview.vercel.app',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    }
    r = client.options(f"{BASE_URL}/api/v1/auth/token/", headers=headers)
    cors_allowed = 'access-control-allow-origin' in [h.lower() for h in r.headers]
    record('/api/v1/auth/token/ (CORS OPTIONS)', 'OPTIONS', r.status_code, 200, r.status_code == 200 and cors_allowed, 'Access-Control-Allow-Origin header present', dict(r.headers))
except Exception as e:
    record('/api/v1/auth/token/ (CORS)', 'OPTIONS', 0, 200, False, 'CORS preflight 200', str(e))

# 4. Candidate Registration
cand_email = f"candidate_{RUN_ID}@testinterview.org"
cand_username = f"cand_{RUN_ID}"
cand_pwd = "SecureCandidate123!"

cand_reg_payload = {
    'email': cand_email,
    'username': cand_username,
    'password': cand_pwd,
    'confirm_password': cand_pwd,
    'full_name': f"Candidate Test {RUN_ID}",
    'phone': '+15551234567',
    'place': 'Silicon Valley',
    'city': 'San Jose',
    'state': 'California',
    'pin': '95112'
}

cand_access_token = None
cand_refresh_token = None

try:
    r = client.post(f"{BASE_URL}/api/v1/auth/register/candidate/", json=cand_reg_payload)
    data = r.json() if r.status_code in (200, 201) else r.text
    record('/api/v1/auth/register/candidate/', 'POST', r.status_code, 201, r.status_code == 201, 'User & Profile created with tokens', data)
except Exception as e:
    record('/api/v1/auth/register/candidate/', 'POST', 0, 201, False, '201 Created', str(e))

# 5. Candidate JWT Login (Token Obtain)
try:
    r = client.post(f"{BASE_URL}/api/v1/auth/token/", json={'username': cand_email, 'password': cand_pwd})
    if r.status_code == 200:
        cand_tokens = r.json()
        cand_access_token = cand_tokens.get('access')
        cand_refresh_token = cand_tokens.get('refresh')
        record('/api/v1/auth/token/ (Candidate Login)', 'POST', r.status_code, 200, True, 'access & refresh JWT tokens', {'access_present': bool(cand_access_token), 'role': cand_tokens.get('user', {}).get('role')})
    else:
        record('/api/v1/auth/token/ (Candidate Login)', 'POST', r.status_code, 200, False, '200 OK with tokens', r.text)
except Exception as e:
    record('/api/v1/auth/token/ (Candidate Login)', 'POST', 0, 200, False, '200 OK', str(e))

# 6. Token Refresh
if cand_refresh_token:
    try:
        r = client.post(f"{BASE_URL}/api/v1/auth/token/refresh/", json={'refresh': cand_refresh_token})
        record('/api/v1/auth/token/refresh/', 'POST', r.status_code, 200, r.status_code == 200, 'new access token', r.text)
    except Exception as e:
        record('/api/v1/auth/token/refresh/', 'POST', 0, 200, False, '200 OK', str(e))

# 7. Candidate Current User (/api/v1/auth/me/)
headers_cand = {'Authorization': f'Bearer {cand_access_token}'} if cand_access_token else {}
if cand_access_token:
    try:
        r = client.get(f"{BASE_URL}/api/v1/auth/me/", headers=headers_cand)
        record('/api/v1/auth/me/ (Candidate)', 'GET', r.status_code, 200, r.status_code == 200, 'User profile info', r.text)
    except Exception as e:
        record('/api/v1/auth/me/ (Candidate)', 'GET', 0, 200, False, '200 OK', str(e))

    # 8. Candidate Profile View & Update
    try:
        r = client.get(f"{BASE_URL}/api/v1/candidates/profile/", headers=headers_cand)
        record('/api/v1/candidates/profile/', 'GET', r.status_code, 200, r.status_code == 200, 'Candidate profile details', r.text)
    except Exception as e:
        record('/api/v1/candidates/profile/', 'GET', 0, 200, False, '200 OK', str(e))

    try:
        r = client.put(f"{BASE_URL}/api/v1/candidates/profile/", json={'place': 'San Francisco', 'city': 'San Francisco'}, headers=headers_cand)
        record('/api/v1/candidates/profile/ (Update)', 'PUT', r.status_code, 200, r.status_code == 200, 'Updated candidate profile', r.text)
    except Exception as e:
        record('/api/v1/candidates/profile/ (Update)', 'PUT', 0, 200, False, '200 OK', str(e))

    # 9. Candidate Dashboard
    try:
        r = client.get(f"{BASE_URL}/api/v1/candidates/dashboard/", headers=headers_cand)
        record('/api/v1/candidates/dashboard/', 'GET', r.status_code, 200, r.status_code == 200, 'Candidate dashboard summary stats', r.text)
    except Exception as e:
        record('/api/v1/candidates/dashboard/', 'GET', 0, 200, False, '200 OK', str(e))

# 10. Company Registration
comp_email = f"company_{RUN_ID}@technova.org"
comp_username = f"comp_{RUN_ID}"
comp_pwd = "SecureCompany123!"

comp_reg_payload = {
    'email': comp_email,
    'username': comp_username,
    'password': comp_pwd,
    'confirm_password': comp_pwd,
    'company_name': f"TechNova Global {RUN_ID}",
    'phone': '+15559876543',
    'address': '100 Silicon Blvd, Suite 400',
    'website': 'https://technovaglobal.example.com',
    'description': 'Leading cloud & AI solutions provider'
}

comp_access_token = None
try:
    r = client.post(f"{BASE_URL}/api/v1/auth/register/company/", json=comp_reg_payload)
    data = r.json() if r.status_code in (200, 201) else r.text
    record('/api/v1/auth/register/company/', 'POST', r.status_code, 201, r.status_code == 201, 'Company user & profile created', data)
except Exception as e:
    record('/api/v1/auth/register/company/', 'POST', 0, 201, False, '201 Created', str(e))

# 11. Company Login
try:
    r = client.post(f"{BASE_URL}/api/v1/auth/token/", json={'username': comp_email, 'password': comp_pwd})
    if r.status_code == 200:
        comp_tokens = r.json()
        comp_access_token = comp_tokens.get('access')
        record('/api/v1/auth/token/ (Company Login)', 'POST', r.status_code, 200, True, 'access & refresh JWT tokens', {'access_present': bool(comp_access_token), 'role': comp_tokens.get('user', {}).get('role')})
    else:
        record('/api/v1/auth/token/ (Company Login)', 'POST', r.status_code, 200, False, '200 OK with tokens', r.text)
except Exception as e:
    record('/api/v1/auth/token/ (Company Login)', 'POST', 0, 200, False, '200 OK', str(e))

headers_comp = {'Authorization': f'Bearer {comp_access_token}'} if comp_access_token else {}

# 12. Company Profile & Dashboard
if comp_access_token:
    try:
        r = client.get(f"{BASE_URL}/api/v1/companies/profile/", headers=headers_comp)
        record('/api/v1/companies/profile/', 'GET', r.status_code, 200, r.status_code == 200, 'Company profile details', r.text)
    except Exception as e:
        record('/api/v1/companies/profile/', 'GET', 0, 200, False, '200 OK', str(e))

    try:
        r = client.get(f"{BASE_URL}/api/v1/companies/dashboard/", headers=headers_comp)
        record('/api/v1/companies/dashboard/', 'GET', r.status_code, 200, r.status_code == 200, 'Company dashboard metrics', r.text)
    except Exception as e:
        record('/api/v1/companies/dashboard/', 'GET', 0, 200, False, '200 OK', str(e))

# 13. Company Vacancy Creation (Verification Gate Check)
if comp_access_token:
    vacancy_payload = {
        'title': f'Senior Python / Django Engineer {RUN_ID}',
        'description': 'Develop scalable backend APIs and AI pipelines.',
        'job_type': 'FULL_TIME',
        'experience_years_required': 3,
        'salary_min': 90000,
        'salary_max': 130000,
        'location': 'Remote / San Francisco',
        'skills_required': 'Python, Django, PostgreSQL, Docker',
        'status': 'ACTIVE'
    }
    try:
        r = client.post(f"{BASE_URL}/api/v1/companies/vacancies/", json=vacancy_payload, headers=headers_comp)
        is_expected = r.status_code in (201, 403)
        record('/api/v1/companies/vacancies/ (Verification Gate)', 'POST', r.status_code, 403 if r.status_code == 403 else 201, is_expected, '403 Forbidden (requires verification) or 201 Created', r.text)
    except Exception as e:
        record('/api/v1/companies/vacancies/', 'POST', 0, 403, False, '403 Forbidden', str(e))

# 14. Public Vacancy Listing
try:
    r = client.get(f"{BASE_URL}/api/v1/vacancies/")
    record('/api/v1/vacancies/', 'GET', r.status_code, 200, r.status_code == 200, 'Public vacancy list', r.text)
except Exception as e:
    record('/api/v1/vacancies/', 'GET', 0, 200, False, '200 OK', str(e))

# 15. Candidate Applications List
if cand_access_token:
    try:
        r = client.get(f"{BASE_URL}/api/v1/applications/", headers=headers_cand)
        record('/api/v1/applications/', 'GET', r.status_code, 200, r.status_code == 200, 'Candidate application list', r.text)
    except Exception as e:
        record('/api/v1/applications/', 'GET', 0, 200, False, '200 OK', str(e))

# 16. AI Mock Interview Session Creation
mock_session_id = None
if cand_access_token:
    mock_payload = {
        'job_role': 'Python Django Backend Engineer',
        'category': 'TECHNICAL',
        'difficulty': 'MID',
        'question_count': 3,
        'camera_consent_given': True
    }
    try:
        r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/", json=mock_payload, headers=headers_cand)
        if r.status_code in (200, 201):
            sess_data = r.json()
            mock_session_id = sess_data.get('session', {}).get('id') or sess_data.get('id')
            record('/api/v1/ai-interviews/sessions/', 'POST', r.status_code, 201, bool(mock_session_id), 'Session created in CREATED state', sess_data)
        else:
            record('/api/v1/ai-interviews/sessions/', 'POST', r.status_code, 201, False, '201 Created', r.text)
    except Exception as e:
        record('/api/v1/ai-interviews/sessions/', 'POST', 0, 201, False, '201 Created', str(e))

# 17. Start AI Session (Triggers AI / Gemini Question Generation)
questions_list = []
if cand_access_token and mock_session_id:
    try:
        r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/start/", headers=headers_cand)
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/start/', 'POST', r.status_code, 200, r.status_code == 200, 'Session in IN_PROGRESS, questions generated', r.text)
    except Exception as e:
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/start/', 'POST', 0, 200, False, '200 OK', str(e))

    # 18. Retrieve Generated Questions
    try:
        r = client.get(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/questions/", headers=headers_cand)
        if r.status_code == 200:
            questions_list = r.json()
            record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/questions/', 'GET', r.status_code, 200, len(questions_list) > 0, 'List of generated questions', questions_list)
        else:
            record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/questions/', 'GET', r.status_code, 200, False, '200 OK', r.text)
    except Exception as e:
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/questions/', 'GET', 0, 200, False, '200 OK', str(e))

    # 19. Submit Answers to Question
    if questions_list:
        sample_q = questions_list[0]
        q_id = sample_q.get('id')
        ans_payload = {
            'question_id': q_id,
            'answer_text': 'To resolve N+1 queries in Django ORM, I use select_related for single-valued relationships (ForeignKey, OneToOne) which performs an SQL JOIN, and prefetch_related for multi-valued relationships (ManyToMany, reverse ForeignKey) which executes a separate query with an IN clause.',
            'time_taken_seconds': 45
        }
        try:
            r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/submit-answer/", json=ans_payload, headers=headers_cand)
            record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/submit-answer/', 'POST', r.status_code, 201, r.status_code in (200, 201), 'Answer recorded', r.text)
        except Exception as e:
            record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/submit-answer/', 'POST', 0, 201, False, '201 Created', str(e))

    # 20. Camera Telemetry Stream
    telemetry_payload = {
        'centered_posture_percentage': 91.5,
        'head_stability_score': 86.0,
        'eye_contact_ratio': 88.0,
        'frames_processed': 40
    }
    try:
        r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/camera-telemetry/", json=telemetry_payload, headers=headers_cand)
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/camera-telemetry/', 'POST', r.status_code, 200, r.status_code == 200, 'Camera telemetry recorded', r.text)
    except Exception as e:
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/camera-telemetry/', 'POST', 0, 200, False, '200 OK', str(e))

    # 21. Complete Session (Triggers AI Evaluation)
    try:
        r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/complete/", headers=headers_cand)
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/complete/', 'POST', r.status_code, 200, r.status_code == 200, 'Session COMPLETED with scores and feedback', r.text)
    except Exception as e:
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/complete/', 'POST', 0, 200, False, '200 OK', str(e))

    # 22. View Session Results
    try:
        r = client.get(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/results/", headers=headers_cand)
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/results/', 'GET', r.status_code, 200, r.status_code == 200, 'Complete evaluation result breakdown', r.text)
    except Exception as e:
        record(f'/api/v1/ai-interviews/sessions/{mock_session_id}/results/', 'GET', 0, 200, False, '200 OK', str(e))

    # 23. Download PDF Report
    try:
        r = client.get(f"{BASE_URL}/api/v1/reports/mock-interviews/{mock_session_id}/pdf/", headers=headers_cand)
        is_pdf = r.status_code == 200 and r.headers.get('content-type', '').startswith('application/pdf')
        record(f'/api/v1/reports/mock-interviews/{mock_session_id}/pdf/', 'GET', r.status_code, 200, is_pdf, 'PDF binary stream with application/pdf header', f"Content-Type: {r.headers.get('content-type')}, bytes: {len(r.content)}")
    except Exception as e:
        record(f'/api/v1/reports/mock-interviews/{mock_session_id}/pdf/', 'GET', 0, 200, False, '200 OK', str(e))

# 24. Feedback API
if cand_access_token:
    feedback_payload = {
        'feedback_text': 'Excellent AI Mock Interview experience. Immediate scoring and evaluation were very helpful.'
    }
    try:
        r = client.post(f"{BASE_URL}/api/v1/feedback/", json=feedback_payload, headers=headers_cand)
        record('/api/v1/feedback/', 'POST', r.status_code, 201, r.status_code == 201, 'Feedback submitted', r.text)
    except Exception as e:
        record('/api/v1/feedback/', 'POST', 0, 201, False, '201 Created', str(e))

    try:
        r = client.get(f"{BASE_URL}/api/v1/feedback/", headers=headers_cand)
        record('/api/v1/feedback/', 'GET', r.status_code, 200, r.status_code == 200, 'My submitted feedback list', r.text)
    except Exception as e:
        record('/api/v1/feedback/', 'GET', 0, 200, False, '200 OK', str(e))

# 25. Complaint API
if cand_access_token:
    complaint_payload = {
        'complaint_text': 'Inquiry regarding interview rescheduling guidelines and technical evaluation criteria.'
    }
    try:
        r = client.post(f"{BASE_URL}/api/v1/complaints/", json=complaint_payload, headers=headers_cand)
        record('/api/v1/complaints/', 'POST', r.status_code, 201, r.status_code == 201, 'Complaint/Inquiry registered', r.text)
    except Exception as e:
        record('/api/v1/complaints/', 'POST', 0, 201, False, '201 Created', str(e))

    try:
        r = client.get(f"{BASE_URL}/api/v1/complaints/", headers=headers_cand)
        record('/api/v1/complaints/', 'GET', r.status_code, 200, r.status_code == 200, 'My complaints list', r.text)
    except Exception as e:
        record('/api/v1/complaints/', 'GET', 0, 200, False, '200 OK', str(e))

# 26. Notifications API
if cand_access_token:
    try:
        r = client.get(f"{BASE_URL}/api/v1/notifications/", headers=headers_cand)
        record('/api/v1/notifications/', 'GET', r.status_code, 200, r.status_code == 200, 'Notifications list', r.text)
    except Exception as e:
        record('/api/v1/notifications/', 'GET', 0, 200, False, '200 OK', str(e))

    try:
        r = client.post(f"{BASE_URL}/api/v1/notifications/mark-all-read/", headers=headers_cand)
        record('/api/v1/notifications/mark-all-read/', 'POST', r.status_code, 200, r.status_code == 200, 'Mark all notifications read', r.text)
    except Exception as e:
        record('/api/v1/notifications/mark-all-read/', 'POST', 0, 200, False, '200 OK', str(e))

# 27. Legacy Flutter Compatibility Endpoints (/myapp/...)
try:
    r = client.post(f"{BASE_URL}/myapp/User_login/", data={'username': cand_email, 'password': cand_pwd})
    record('/myapp/User_login/ (Legacy Mobile Form-encoded)', 'POST', r.status_code, 200, r.status_code == 200, "{'status': 'ok', 'type': 'candidate'}", r.text)
except Exception as e:
    record('/myapp/User_login/', 'POST', 0, 200, False, '200 OK', str(e))

try:
    r = client.post(f"{BASE_URL}/myapp/user_view_vacancy/")
    record('/myapp/user_view_vacancy/ (Legacy Vacancies)', 'POST', r.status_code, 200, r.status_code == 200, "{'status': 'ok', 'data': [...]}", r.text)
except Exception as e:
    record('/myapp/user_view_vacancy/', 'POST', 0, 200, False, '200 OK', str(e))

# 28. Role-based Permission Enforcement (Security check)
# Candidate attempting to post a vacancy (Company-only)
if cand_access_token:
    try:
        r = client.post(f"{BASE_URL}/api/v1/companies/vacancies/", json={'title': 'Hacker Job'}, headers=headers_cand)
        record('/api/v1/companies/vacancies/ (Candidate RBAC test)', 'POST', r.status_code, 403, r.status_code == 403, '403 Forbidden (Only companies can post)', r.text)
    except Exception as e:
        record('/api/v1/companies/vacancies/ (Candidate RBAC test)', 'POST', 0, 403, False, '403 Forbidden', str(e))

# Company attempting to submit a candidate interview answer
if comp_access_token and mock_session_id:
    try:
        r = client.post(f"{BASE_URL}/api/v1/ai-interviews/sessions/{mock_session_id}/submit-answer/", json={'question_id': 1, 'answer_text': 'test'}, headers=headers_comp)
        record('/api/v1/ai-interviews/.../submit-answer/ (Company RBAC test)', 'POST', r.status_code, 403, r.status_code == 403, '403 Forbidden (Only candidate owner)', r.text)
    except Exception as e:
        record('/api/v1/ai-interviews/.../submit-answer/ (Company RBAC test)', 'POST', 0, 403, False, '403 Forbidden', str(e))

# Unauthenticated access to protected endpoint
try:
    r = client.get(f"{BASE_URL}/api/v1/auth/me/")
    record('/api/v1/auth/me/ (Unauthenticated)', 'GET', r.status_code, 401, r.status_code == 401, '401 Unauthorized', r.text)
except Exception as e:
    record('/api/v1/auth/me/ (Unauthenticated)', 'GET', 0, 401, False, '401 Unauthorized', str(e))

print("\n=== COMPLETE PRODUCTION API TEST RESULTS ===")
total = len(results)
passed_count = sum(1 for x in results if x['passed'])
failed_count = total - passed_count
print(f"Total Tests Run: {total}")
print(f"Passed: {passed_count}")
print(f"Failed: {failed_count}")

# Print JSON summary for reporting
import json
with open('c:/Users/LOQ/Downloads/AI-Based-Mock-Interview-Preparation-System-main/AI-Based-Mock-Interview-Preparation-System-main/api_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved complete test report to api_test_results.json")
