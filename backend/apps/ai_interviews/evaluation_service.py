import os
import json
import logging
from decimal import Decimal
from typing import Dict, Any
from django.conf import settings
from django.utils import timezone
from .models import AIMockSession, AIMockAnswer

logger = logging.getLogger(__name__)


def evaluate_mock_session(session: AIMockSession) -> Dict[str, Any]:
    """
    Evaluates all submitted answers for an AIMockSession.
    Computes per-question scores (Relevance, Technical Accuracy, Completeness, Clarity),
    as well as the session aggregate overall score, summary feedback, strengths, and areas for improvement.
    Transitions session status to COMPLETED.
    """
    answers = session.answers.all().select_related('question')
    if not answers.exists():
        # No answers submitted
        session.overall_score = Decimal('0.0')
        session.status = AIMockSession.Status.COMPLETED
        session.summary_feedback = "The interview session was completed without submitting answers to the questions."
        session.completed_at = timezone.now()
        session.save()
        return {
            'overall_score': 0.0,
            'summary_feedback': session.summary_feedback,
            'total_questions': session.questions.count(),
            'total_answered': 0,
        }

    question_scores = []
    all_strengths = []
    all_improvements = []

    for answer in answers:
        eval_result = evaluate_single_answer(answer)
        answer.relevance_score = Decimal(str(eval_result['relevance_score']))
        answer.accuracy_score = Decimal(str(eval_result['accuracy_score']))
        answer.completeness_score = Decimal(str(eval_result['completeness_score']))
        answer.clarity_score = Decimal(str(eval_result['clarity_score']))
        answer.overall_question_score = Decimal(str(eval_result['overall_question_score']))
        answer.feedback = eval_result['feedback']
        answer.strengths = eval_result['strengths']
        answer.improvement_areas = eval_result['improvement_areas']
        answer.save()

        question_scores.append(float(answer.overall_question_score))
        if answer.strengths:
            all_strengths.append(answer.strengths)
        if answer.improvement_areas:
            all_improvements.append(answer.improvement_areas)

    total_questions = session.questions.count()
    answered_count = len(question_scores)

    # Average score across all session questions (unanswered questions counted as 0)
    if total_questions > 0:
        sum_scores = sum(question_scores)
        overall_avg = round(sum_scores / total_questions, 2)
    else:
        overall_avg = 0.0

    session.overall_score = Decimal(str(overall_avg))
    session.status = AIMockSession.Status.COMPLETED
    session.completed_at = timezone.now()

    # Formulate session summary
    if overall_avg >= 80:
        perf_tier = "Strong Performance"
        summary_intro = f"The candidate demonstrated strong domain expertise in {session.job_role} with articulate explanations and sound conceptual depth."
    elif overall_avg >= 60:
        perf_tier = "Satisfactory Performance"
        summary_intro = f"The candidate showed solid foundational understanding for {session.job_role}, with room to elaborate more deeply on technical trade-offs and edge cases."
    else:
        perf_tier = "Needs Development"
        summary_intro = f"The candidate answered fundamental aspects of {session.job_role}, but requires further preparation on core terminology, structured responses, and complete examples."

    session.summary_feedback = f"[{perf_tier} - {overall_avg}%] {summary_intro}"
    session.strengths_summary = " • ".join(all_strengths[:3]) if all_strengths else "Demonstrated general familiarity with role concepts."
    session.improvements_summary = " • ".join(all_improvements[:3]) if all_improvements else "Provide more concrete real-world examples and structured STAR method explanations."
    session.save()

    return {
        'session_id': session.id,
        'overall_score': float(session.overall_score),
        'summary_feedback': session.summary_feedback,
        'strengths_summary': session.strengths_summary,
        'improvements_summary': session.improvements_summary,
        'total_questions': total_questions,
        'total_answered': answered_count,
    }


def evaluate_single_answer(answer: AIMockAnswer) -> Dict[str, Any]:
    """
    Evaluates a single answer using Gemini API if configured,
    or our high-precision NLP Heuristic Evaluator when offline.
    """
    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)

    if api_key and api_key.strip() and api_key != 'your_gemini_api_key_here':
        try:
            return _evaluate_with_gemini(
                api_key=api_key.strip(),
                question_text=answer.question.question_text,
                rubric=answer.question.evaluation_rubric,
                expected_keywords=answer.question.expected_keywords,
                answer_text=answer.answer_text
            )
        except Exception as e:
            logger.warning(f"Gemini API answer evaluation failed: {e}. Falling back to NLP evaluator.")

    return _evaluate_with_nlp_heuristics(
        question_text=answer.question.question_text,
        rubric=answer.question.evaluation_rubric,
        expected_keywords=answer.question.expected_keywords,
        answer_text=answer.answer_text
    )


def _evaluate_with_gemini(api_key: str, question_text: str, rubric: str, expected_keywords: str, answer_text: str) -> Dict[str, Any]:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
You are an objective, expert technical interviewer evaluating a candidate's response.
Question Asked:
{question_text}

Evaluation Rubric:
{rubric}

Expected Key Concepts:
{expected_keywords}

Candidate Answer:
{answer_text}

Evaluate the response across the following criteria and return ONLY a valid JSON object:
1. "relevance_score": number from 0.0 to 10.0 (how directly the answer addresses the question).
2. "accuracy_score": number from 0.0 to 10.0 (technical correctness and precision).
3. "completeness_score": number from 0.0 to 10.0 (breadth, depth, and handling key nuances).
4. "clarity_score": number from 0.0 to 10.0 (organization, conciseness, and communication quality).
5. "overall_question_score": number from 0.0 to 100.0 (weighted composite score).
6. "feedback": 2-3 sentences of constructive feedback.
7. "strengths": 1-2 positive aspects observed.
8. "improvement_areas": 1-2 specific suggestions for improvement.
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    data = json.loads(raw)
    return {
        'relevance_score': round(float(data.get('relevance_score', 7.5)), 1),
        'accuracy_score': round(float(data.get('accuracy_score', 7.5)), 1),
        'completeness_score': round(float(data.get('completeness_score', 7.0)), 1),
        'clarity_score': round(float(data.get('clarity_score', 8.0)), 1),
        'overall_question_score': round(float(data.get('overall_question_score', 75.0)), 2),
        'feedback': str(data.get('feedback', 'Answer addressed the core principles of the question.')),
        'strengths': str(data.get('strengths', 'Clear conceptual articulation.')),
        'improvement_areas': str(data.get('improvement_areas', 'Include more specific practical implementation details.')),
    }


def _evaluate_with_nlp_heuristics(question_text: str, rubric: str, expected_keywords: str, answer_text: str) -> Dict[str, Any]:
    """
    Domain-specific NLP heuristic evaluator based on token overlap, keyword match ratio,
    length completeness, and clarity metrics.
    """
    clean_ans = answer_text.strip().lower()
    words = clean_ans.split()
    word_count = len(words)

    # 1. Keyword Overlap
    matched_keywords = []
    missing_keywords = []
    expected_list = [k.strip().lower() for k in expected_keywords.split(',') if k.strip()]

    if expected_list:
        for kw in expected_list:
            if kw in clean_ans or any(token in clean_ans for token in kw.split()):
                matched_keywords.append(kw)
            else:
                missing_keywords.append(kw)
        keyword_ratio = len(matched_keywords) / len(expected_list)
    else:
        keyword_ratio = 0.7

    # 2. Completeness (Word count curve: optimal between 40 and 150 words)
    if word_count < 10:
        completeness = 3.0
    elif word_count < 25:
        completeness = 5.5
    elif word_count < 60:
        completeness = 7.5
    elif word_count <= 200:
        completeness = 9.0
    else:
        completeness = 8.5  # Slightly verbose

    # 3. Accuracy & Relevance based on keyword coverage
    accuracy = round(max(3.0, min(9.5, 4.0 + (keyword_ratio * 5.5))), 1)
    relevance = round(max(4.0, min(9.8, 4.5 + (keyword_ratio * 5.0))), 1)
    clarity = round(max(4.0, min(9.5, 6.0 + (0.5 if word_count >= 25 else -1.0))), 1)

    # Composite overall score out of 100
    # Weights: Accuracy 35%, Relevance 25%, Completeness 25%, Clarity 15%
    overall = (
        (float(accuracy) * 3.5) +
        (float(relevance) * 2.5) +
        (float(completeness) * 2.5) +
        (float(clarity) * 1.5)
    )
    overall_score = round(float(overall), 2)

    # Feedback synthesis
    if matched_keywords:
        strengths = f"Effectively referenced key concepts: {', '.join(matched_keywords[:3])}."
    else:
        strengths = "Provided a direct conversational response to the prompt."

    if missing_keywords:
        improvement = f"Could further strengthen the answer by elaborating on: {', '.join(missing_keywords[:2])}."
        feedback = f"Good foundational explanation. To achieve top marks, incorporate specific technical context regarding {', '.join(missing_keywords[:2])}."
    else:
        improvement = "Elaborate with specific production metrics and architectural trade-offs."
        feedback = "Thorough and well-structured answer demonstrating strong subject matter familiarity."

    return {
        'relevance_score': float(relevance),
        'accuracy_score': float(accuracy),
        'completeness_score': float(completeness),
        'clarity_score': float(clarity),
        'overall_question_score': float(overall_score),
        'feedback': feedback,
        'strengths': strengths,
        'improvement_areas': improvement,
    }
