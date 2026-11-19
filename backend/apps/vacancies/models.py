from django.db import models
from django.utils import timezone
from apps.companies.models import CompanyProfile
from django.utils.translation import gettext_lazy as _


class Vacancy(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        CLOSED = 'CLOSED', _('Closed')
        EXPIRED = 'EXPIRED', _('Expired')

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name=_('Company')
    )
    position = models.CharField(_('Job Position / Title'), max_length=255, db_index=True)
    description = models.TextField(_('Job Description'))
    required_qualifications = models.TextField(_('Required Qualifications'), blank=True)
    required_skills = models.TextField(_('Required Skills'), blank=True)
    experience_years = models.IntegerField(_('Required Experience (Years)'), default=0)
    location = models.CharField(_('Job Location'), max_length=255, default='Remote')
    salary_range = models.CharField(_('Salary Range'), max_length=100, blank=True)
    no_of_vacancy = models.PositiveIntegerField(_('Number of Openings'), default=1)
    start_date = models.DateField(_('Start Date'), default=timezone.localdate)
    application_deadline = models.DateField(_('Application Deadline'), db_index=True)
    status = models.CharField(
        _('Job Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Job Vacancy')
        verbose_name_plural = _('Job Vacancies')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.position} at {self.company.company_name} ({self.status})"

    @property
    def is_expired(self):
        return self.application_deadline < timezone.now().date()
