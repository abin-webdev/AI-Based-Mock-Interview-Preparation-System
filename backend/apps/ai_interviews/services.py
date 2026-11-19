import os
import json
import logging
from typing import List, Dict, Any
from django.conf import settings
from .models import AIMockSession, AIMockQuestion

logger = logging.getLogger(__name__)


def generate_mock_interview_questions(session: AIMockSession) -> List[AIMockQuestion]:
    """
    Generates interview questions dynamically for an AIMockSession based on:
    - job_role
    - category (TECHNICAL, HR, GENERAL, JOB_SPECIFIC)
    - difficulty (JUNIOR, MID, SENIOR)
    - question_count

    Uses Google Gemini API when GEMINI_API_KEY is configured in environment.
    Falls back gracefully to intelligent domain-based question templates when offline or without key.
    """
    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
    questions_data = []

    if api_key and api_key.strip() and api_key != 'your_gemini_api_key_here':
        try:
            questions_data = _generate_with_gemini(
                api_key=api_key.strip(),
                job_role=session.job_role,
                category=session.category,
                difficulty=session.difficulty,
                count=session.question_count
            )
        except Exception as e:
            logger.warning(f"Gemini API question generation failed: {e}. Falling back to domain generator.")
            questions_data = []

    # If Gemini returned empty or failed or no API key, use domain-specific dynamic fallback
    if not questions_data:
        questions_data = _generate_domain_questions(
            job_role=session.job_role,
            category=session.category,
            difficulty=session.difficulty,
            count=session.question_count
        )

    # Persist questions to database
    # Clear any previous generated questions if re-generating
    session.questions.all().delete()

    created_questions = []
    for idx, q_data in enumerate(questions_data, start=1):
        question = AIMockQuestion.objects.create(
            session=session,
            question_number=idx,
            question_text=q_data['question_text'],
            category=q_data.get('category', session.category),
            expected_keywords=q_data.get('expected_keywords', ''),
            evaluation_rubric=q_data.get('evaluation_rubric', '')
        )
        created_questions.append(question)

    return created_questions


def _generate_with_gemini(api_key: str, job_role: str, category: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    # Prefer gemini-1.5-flash or gemini-pro
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
You are an expert technical interviewer and hiring manager conducting a mock interview.
Generate exactly {count} professional interview questions for a candidate with the following parameters:
- Target Job Role: {job_role}
- Interview Category: {category} (Technical / HR / Behavioral / Job Specific)
- Difficulty Level: {difficulty} (Junior / Mid / Senior)

Return ONLY a valid JSON array of objects with no markdown wrapping or preamble. Each object must contain:
1. "question_text": The interview question as asked by the interviewer.
2. "category": "{category}"
3. "expected_keywords": A comma-separated string of 4-6 key concepts/technologies expected in an ideal response.
4. "evaluation_rubric": Concise criteria (2-3 sentences) detailing what a complete, high-scoring answer must address.

Example format:
[
  {{
    "question_text": "How do you handle database connection pooling in a high-concurrency web application?",
    "category": "TECHNICAL",
    "expected_keywords": "connection pool, thread safety, latency, timeouts, PgBouncer",
    "evaluation_rubric": "Evaluates knowledge of connection overhead, pool configuration, and mitigating resource exhaustion."
  }}
]
"""
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Clean backticks if Gemini wrapped in ```json ... ```
    if raw_text.startswith('```'):
        lines = raw_text.splitlines()
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    parsed = json.loads(raw_text)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return parsed[:count]
    return []


def _generate_domain_questions(job_role: str, category: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
    """
    Intelligent domain-specific fallback generator ensuring realistic, tailored interview questions
    based on role, category, and difficulty tier without requiring external network access.
    """
    role_lower = job_role.lower()

    if category == AIMockSession.Category.TECHNICAL or 'tech' in category.lower():
        if any(w in role_lower for w in ['python', 'django', 'backend', 'api']):
            pool = [
                {
                    "question_text": f"In {job_role}, how do you optimize Django ORM queries to prevent the N+1 database query problem?",
                    "category": "TECHNICAL",
                    "expected_keywords": "select_related, prefetch_related, database hits, SQL joins, query optimization",
                    "evaluation_rubric": "Candidate must explain the difference between select_related (foreign keys/SQL join) and prefetch_related (M2M/reverse FK) and how profiling queries improves latency."
                },
                {
                    "question_text": f"Explain the architectural trade-offs between monolithic and microservice architectures for a backend in {job_role}.",
                    "category": "TECHNICAL",
                    "expected_keywords": "scalability, deployment complexity, latency, service discovery, database per service",
                    "evaluation_rubric": "Should compare operational overhead, independent deployment, data consistency, and organizational alignment."
                },
                {
                    "question_text": "How do you secure RESTful APIs against common vulnerabilities like CSRF, injection, and broken object-level authorization (BOLA)?",
                    "category": "TECHNICAL",
                    "expected_keywords": "OWASP, parameterized queries, JWT, RBAC, input validation, rate limiting",
                    "evaluation_rubric": "Candidate must touch upon input validation, token verification, permissions checking on individual model instances, and rate limiting."
                },
                {
                    "question_text": "Describe your strategy for implementing caching in a high-traffic web application. Which layers do you cache at?",
                    "category": "TECHNICAL",
                    "expected_keywords": "Redis, Memcached, CDN, HTTP cache-control, cache invalidation, cache stampede",
                    "evaluation_rubric": "Candidate should mention CDN/edge caching, database query caching, in-memory caching, and explain cache invalidation strategies."
                },
                {
                    "question_text": "How do asynchronous task queues (like Celery or Redis Queues) fit into your system architecture, and how do you handle task failures and retries?",
                    "category": "TECHNICAL",
                    "expected_keywords": "message broker, idempotency, exponential backoff, dead letter queue, task workers",
                    "evaluation_rubric": "Should address separating long-running background tasks from the request-response cycle, idempotency, and dead-letter queues."
                },
                {
                    "question_text": f"As a {difficulty} engineer, how do you approach database schema migrations in zero-downtime deployment pipelines?",
                    "category": "TECHNICAL",
                    "expected_keywords": "backward compatibility, non-blocking migrations, zero downtime, multi-step deploy, blue-green",
                    "evaluation_rubric": "Must explain multi-phase deployments: add nullable columns, deploy code, backfill data, add constraints, remove old columns."
                }
            ]
        elif any(w in role_lower for w in ['flutter', 'mobile', 'frontend', 'android', 'ios']):
            pool = [
                {
                    "question_text": f"In {job_role}, explain Flutter's rendering pipeline and how the Widget, Element, and RenderObject trees interact.",
                    "category": "TECHNICAL",
                    "expected_keywords": "Widget tree, Element tree, RenderObject, rebuild, layout, paint",
                    "evaluation_rubric": "Must explain that widgets are immutable blueprints, elements manage lifecycle and reconciliation, and RenderObjects handle layout and painting."
                },
                {
                    "question_text": "Compare state management approaches in Flutter (e.g., Provider, Riverpod, BLoC). When would you choose one over the others?",
                    "category": "TECHNICAL",
                    "expected_keywords": "BLoC, Riverpod, Provider, reactive programming, streams, testability, separation of concerns",
                    "evaluation_rubric": "Candidate should discuss separation of UI and business logic, stream handling, boilerplate vs maintainability, and testability."
                },
                {
                    "question_text": "How do you optimize Flutter app performance to consistently achieve 60/120 FPS without jank?",
                    "category": "TECHNICAL",
                    "expected_keywords": "const constructors, repainting boundaries, devtools profiler, build method overhead, lazy loading",
                    "evaluation_rubric": "Candidate must mention minimizing build method work, using const constructors, RepaintBoundary, and optimizing image/list rendering."
                },
                {
                    "question_text": "How do you handle asynchronous data, offline synchronization, and caching in a mobile application?",
                    "category": "TECHNICAL",
                    "expected_keywords": "SharedPreferences, SQLite/Hive, FutureBuilder, StreamBuilder, connectivity status, optimistic UI",
                    "evaluation_rubric": "Should cover local database persistence, local-first cache, handling network drops, and graceful sync conflict resolution."
                },
                {
                    "question_text": "How do you implement secure storage and authentication tokens on mobile devices?",
                    "category": "TECHNICAL",
                    "expected_keywords": "flutter_secure_storage, Keychain, KeyStore, biometric auth, refresh token rotation",
                    "evaluation_rubric": "Candidate must discuss iOS Keychain and Android KeyStore, avoiding plaintext token storage, and secure token refresh flows."
                }
            ]
        else:
            # Generic Technical
            pool = [
                {
                    "question_text": f"What are the core technical principles and best design practices you apply when building systems for {job_role}?",
                    "category": "TECHNICAL",
                    "expected_keywords": "SOLID principles, modularity, test coverage, scalability, maintainability",
                    "evaluation_rubric": "Candidate should demonstrate familiarity with software design patterns, architectural modularity, and clean code principles."
                },
                {
                    "question_text": f"Can you walk through a complex technical problem you solved in {job_role} and explain how you diagnosed the root cause?",
                    "category": "TECHNICAL",
                    "expected_keywords": "root cause analysis, logs, profiling, debugging, metrics, post-mortem",
                    "evaluation_rubric": "Looks for structured diagnostic methodology, data-driven debugging, and preventive measures implemented."
                },
                {
                    "question_text": "Explain your approach to automated testing and continuous integration in a production engineering team.",
                    "category": "TECHNICAL",
                    "expected_keywords": "unit tests, integration tests, CI/CD pipelines, regression testing, mock objects",
                    "evaluation_rubric": "Candidate should explain the test pyramid, automated linting, test-driven development, and staging environments."
                },
                {
                    "question_text": "How do you design scalable APIs that balance performance, usability, and backward compatibility?",
                    "category": "TECHNICAL",
                    "expected_keywords": "versioning, pagination, idempotency, rate limiting, payload design",
                    "evaluation_rubric": "Should cover semantic versioning, efficient pagination strategies, and contract testing."
                },
                {
                    "question_text": f"For a {difficulty} level {job_role}, how do you evaluate and introduce new technologies or libraries into an existing codebase?",
                    "category": "TECHNICAL",
                    "expected_keywords": "POC, risk assessment, license compliance, community maintenance, migration path",
                    "evaluation_rubric": "Candidate must discuss proof-of-concept testing, long-term maintenance implications, security auditing, and team adoption."
                }
            ]
    elif category == AIMockSession.Category.HR or 'hr' in category.lower():
        pool = [
            {
                "question_text": f"Why are you interested in pursuing the {job_role} position, and what unique value do you bring to our team?",
                "category": "HR",
                "expected_keywords": "motivation, alignment, culture fit, long-term goals, past achievements",
                "evaluation_rubric": "Candidate should articulate clear self-awareness, alignment with organizational mission, and concrete strengths."
            },
            {
                "question_text": "Describe a situation where you had a disagreement with a team member or stakeholder. How did you resolve it?",
                "category": "HR",
                "expected_keywords": "conflict resolution, active listening, empathy, consensus, professional communication",
                "evaluation_rubric": "STAR format (Situation, Task, Action, Result). Demonstrates emotional intelligence and collaborative mindset."
            },
            {
                "question_text": "How do you manage high-pressure deadlines and prioritize competing tasks across multiple deliverables?",
                "category": "HR",
                "expected_keywords": "prioritization, time management, communication, delegation, boundary setting",
                "evaluation_rubric": "Evaluates proactive status communication, triage methodology, and maintaining composure and quality under pressure."
            },
            {
                "question_text": f"Where do you see your career progression as a {job_role} over the next three to five years?",
                "category": "HR",
                "expected_keywords": "career growth, leadership, technical mastery, mentorship, continuous learning",
                "evaluation_rubric": "Candidate should convey ambition, realistic milestones, desire for skill advancement, and commitment."
            },
            {
                "question_text": "Tell me about a time when a project you were working on failed or didn't meet expectations. What did you learn?",
                "category": "HR",
                "expected_keywords": "ownership, accountability, resilience, retrospectives, actionable learning",
                "evaluation_rubric": "Examines willingness to take ownership without deflecting blame, and applying learnings to future efforts."
            }
        ]
    else:
        # General / Behavioral / Job Specific
        pool = [
            {
                "question_text": f"Can you provide an overview of your relevant background and how your past experiences prepare you for {job_role}?",
                "category": "GENERAL",
                "expected_keywords": "background, project experience, key skills, industry knowledge, achievements",
                "evaluation_rubric": "Candidate should deliver a structured summary connecting their previous accomplishments directly to the requirements of the role."
            },
            {
                "question_text": "Describe a time when you had to learn an unfamiliar technology or domain on a tight schedule. What was your strategy?",
                "category": "GENERAL",
                "expected_keywords": "quick learner, documentation, tutorials, building prototypes, asking questions",
                "evaluation_rubric": "Assesses learning agility, resourcefulness, and ability to translate new knowledge into working results quickly."
            },
            {
                "question_text": "How do you ensure clear communication when explaining complex technical concepts to non-technical stakeholders?",
                "category": "GENERAL",
                "expected_keywords": "analogy, simplification, user impact, active listening, business value",
                "evaluation_rubric": "Demonstrates audience awareness, avoiding jargon, and linking technical decisions to business outcomes."
            },
            {
                "question_text": f"What steps do you take as a {difficulty} {job_role} to maintain high standards of code review and engineering quality?",
                "category": "GENERAL",
                "expected_keywords": "code reviews, constructive feedback, style guides, automated linting, mentoring",
                "evaluation_rubric": "Candidate should emphasize constructive feedback, automated quality gates, and fostering an inclusive team culture."
            },
            {
                "question_text": "Describe an instance where you identified a gap or inefficiency in a team process and took initiative to improve it.",
                "category": "GENERAL",
                "expected_keywords": "initiative, process improvement, automation, teamwork, measurable impact",
                "evaluation_rubric": "Looks for proactive leadership, organizational impact, and ability to rally teammates around better practices."
            }
        ]

    # Return up to the requested count
    if count <= len(pool):
        return pool[:count]
    # If more requested than in pool, cycle/repeat with adjusted numbers
    results = []
    for i in range(count):
        item = dict(pool[i % len(pool)])
        results.append(item)
    return results
