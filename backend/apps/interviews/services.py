from apps.interviews.models import InterviewSchedule
from apps.tests_app.models import TestSchedule, TestCandidateAssignment


def validate_scheduling_conflict(candidate, company, date, start_time, end_time, exclude_interview_id=None):
    """
    Checks for scheduling conflicts for candidate or company on the given date and time window.
    Returns (has_conflict: bool, message: str)
    """
    if start_time >= end_time:
        return True, "Start time must be before end time."

    # 1. Check Candidate Interview Conflicts
    candidate_interviews = InterviewSchedule.objects.filter(
        candidate=candidate,
        date=date,
        status__in=['SCHEDULED', 'RESCHEDULED'],
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    if exclude_interview_id:
        candidate_interviews = candidate_interviews.exclude(id=exclude_interview_id)

    if candidate_interviews.exists():
        conflicting = candidate_interviews.first()
        return True, f"Candidate already has a scheduled interview '{conflicting.interview_title}' from {conflicting.start_time} to {conflicting.end_time} on {date}."

    # 2. Check Candidate Test Conflicts
    candidate_tests = TestCandidateAssignment.objects.filter(
        candidate=candidate,
        test__date=date,
        test__status__in=['SCHEDULED', 'IN_PROGRESS'],
        test__start_time__lt=end_time,
        test__end_time__gt=start_time
    )
    if candidate_tests.exists():
        conflicting_test = candidate_tests.first().test
        return True, f"Candidate has a scheduled assessment '{conflicting_test.test_name}' from {conflicting_test.start_time} to {conflicting_test.end_time} on {date}."

    # 3. Check Company Interview Overlap
    company_interviews = InterviewSchedule.objects.filter(
        company=company,
        date=date,
        status__in=['SCHEDULED', 'RESCHEDULED'],
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    if exclude_interview_id:
        company_interviews = company_interviews.exclude(id=exclude_interview_id)

    if company_interviews.exists():
        conflicting = company_interviews.first()
        return True, f"Your company already has an interview scheduled '{conflicting.interview_title}' from {conflicting.start_time} to {conflicting.end_time} on {date}."

    return False, ""
