from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.vacancies.models import Vacancy
from apps.candidates.models import CandidateProfile


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SHORTLISTED = 'SHORTLISTED', _('Shortlisted')
        REJECTED = 'REJECTED', _('Rejected')
        ACCEPTED = 'ACCEPTED', _('Accepted')

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Job Vacancy')
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Candidate')
    )
    resume = models.FileField(
        _('Application Resume'),
        upload_to='application_resumes/',
        blank=True,
        null=True
    )
    cover_letter = models.TextField(_('Cover Letter / Notes'), blank=True)
    status = models.CharField(
        _('Application Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    company_notes = models.TextField(_('Internal Company Notes'), blank=True)
    applied_at = models.DateTimeField(_('Applied Date'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated Date'), auto_now=True)

    class Meta:
        verbose_name = _('Job Application')
        verbose_name_plural = _('Job Applications')
        ordering = ['-applied_at']
        unique_together = ('vacancy', 'candidate')

    def __str__(self):
        return f"Application #{self.id}: {self.candidate.full_name} for {self.vacancy.position} [{self.status}]"
