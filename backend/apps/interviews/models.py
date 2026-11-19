from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.applications.models import Application


class InterviewSchedule(models.Model):
    class InterviewType(models.TextChoices):
        TECHNICAL = 'TECHNICAL', _('Technical Round')
        HR = 'HR', _('HR Round')
        AI_MOCK = 'AI_MOCK', _('AI Mock Interview')
        FINAL = 'FINAL', _('Final Executive Round')

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        RESCHEDULED = 'RESCHEDULED', _('Rescheduled')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='interview_schedules',
        verbose_name=_('Company')
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='interview_schedules',
        verbose_name=_('Candidate')
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interview_schedules',
        verbose_name=_('Job Application')
    )
    interview_title = models.CharField(_('Interview Title'), max_length=255)
    interview_type = models.CharField(
        _('Interview Type'),
        max_length=30,
        choices=InterviewType.choices,
        default=InterviewType.TECHNICAL
    )
    date = models.DateField(_('Interview Date'), db_index=True)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    meeting_link = models.CharField(_('Meeting Link / Platform URL'), max_length=500, blank=True)
    location = models.CharField(_('Location / Mode'), max_length=255, default='Online Video Call')
    status = models.CharField(
        _('Interview Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True
    )
    cancellation_reason = models.TextField(_('Cancellation Reason'), blank=True)
    notes = models.TextField(_('Interviewer Notes'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Interview Schedule')
        verbose_name_plural = _('Interview Schedules')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.interview_title}: {self.candidate.full_name} with {self.company.company_name} on {self.date}"
