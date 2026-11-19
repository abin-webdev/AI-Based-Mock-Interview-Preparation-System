from django.db import models
from django.conf import settings
from apps.companies.models import CompanyProfile
from django.utils.translation import gettext_lazy as _


class Complaint(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_REVIEW = 'IN_REVIEW', _('In Review')
        RESOLVED = 'RESOLVED', _('Resolved')
        REJECTED = 'REJECTED', _('Rejected')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_filed',
        verbose_name=_('Filed by User')
    )
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name=_('Against Company')
    )
    complaint_text = models.TextField(_('Complaint Description'))
    status = models.CharField(
        _('Complaint Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    reply = models.TextField(_('Admin / Company Reply'), blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_replied',
        verbose_name=_('Replied by Admin')
    )
    replied_at = models.DateTimeField(_('Replied At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Complaint')
        verbose_name_plural = _('Complaints')
        ordering = ['-created_at']

    def __str__(self):
        target = self.company.company_name if self.company else "General"
        return f"Complaint #{self.id} by {self.user.email} against {target} [{self.status}]"
