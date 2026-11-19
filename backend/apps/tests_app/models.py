from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.companies.models import CompanyProfile
from apps.vacancies.models import Vacancy
from apps.candidates.models import CandidateProfile
from apps.applications.models import Application


class TestSchedule(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='test_schedules',
        verbose_name=_('Company')
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_schedules',
        verbose_name=_('Job Vacancy')
    )
    test_name = models.CharField(_('Test Name'), max_length=255)
    test_type = models.CharField(_('Test Type'), max_length=100, default='Online Assessment')
    date = models.DateField(_('Test Date'), db_index=True)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    duration_minutes = models.PositiveIntegerField(_('Duration (Minutes)'), default=60)
    total_marks = models.PositiveIntegerField(_('Total Marks'), default=100)
    pass_marks = models.PositiveIntegerField(_('Pass Marks'), default=50)
    instructions = models.TextField(_('Instructions'), blank=True)
    status = models.CharField(
        _('Test Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Test Schedule')
        verbose_name_plural = _('Test Schedules')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.test_name} ({self.date} {self.start_time}-{self.end_time})"


class TestCandidateAssignment(models.Model):
    class Attendance(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ATTENDED = 'ATTENDED', _('Attended')
        ABSENT = 'ABSENT', _('Absent')

    test = models.ForeignKey(
        TestSchedule,
        on_delete=models.CASCADE,
        related_name='candidate_assignments',
        verbose_name=_('Test Schedule')
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='test_assignments',
        verbose_name=_('Candidate')
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_assignments',
        verbose_name=_('Application')
    )
    attendance_status = models.CharField(
        _('Attendance Status'),
        max_length=20,
        choices=Attendance.choices,
        default=Attendance.PENDING
    )
    score = models.DecimalField(_('Score'), max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(_('Remarks'), blank=True)
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Test Candidate Assignment')
        verbose_name_plural = _('Test Candidate Assignments')
        unique_together = ('test', 'candidate')

    def __str__(self):
        return f"{self.candidate.full_name} assigned to {self.test.test_name}"
