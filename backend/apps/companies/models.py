from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class CompanyProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending Verification')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_profile',
        verbose_name=_('User Account')
    )
    company_name = models.CharField(_('Company Name'), max_length=255, db_index=True)
    email = models.EmailField(_('Official Email'), max_length=255)
    phone = models.CharField(_('Phone Number'), max_length=50)
    address = models.TextField(_('Address'))
    website = models.URLField(_('Website URL'), max_length=255, blank=True)
    description = models.TextField(_('Company Description'), blank=True)
    logo = models.ImageField(_('Company Logo'), upload_to='company_logos/', blank=True, null=True)
    registration_document = models.FileField(
        _('Registration Document'),
        upload_to='company_docs/',
        blank=True,
        null=True
    )
    verification_status = models.CharField(
        _('Verification Status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    rejection_reason = models.TextField(_('Rejection / Suspension Reason'), blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_companies',
        verbose_name=_('Verified By')
    )
    verified_at = models.DateTimeField(_('Verified At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Company Profile')
        verbose_name_plural = _('Company Profiles')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} [{self.verification_status}]"

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.APPROVED


class CompanyReview(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Company')
    )
    candidate = models.ForeignKey(
        'candidates.CandidateProfile',
        on_delete=models.CASCADE,
        related_name='company_reviews',
        verbose_name=_('Candidate')
    )
    rating = models.DecimalField(_('Rating (1-5)'), max_digits=3, decimal_places=1, default=5.0)
    review = models.TextField(_('Review Text'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Company Review')
        verbose_name_plural = _('Company Reviews')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review ({self.rating}★) for {self.company.company_name} by {self.candidate.full_name}"
