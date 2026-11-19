from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate_profile',
        verbose_name=_('User Account')
    )
    full_name = models.CharField(_('Full Name'), max_length=255, db_index=True)
    phone = models.CharField(_('Phone Number'), max_length=50, blank=True)
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    gender = models.CharField(_('Gender'), max_length=20, blank=True)
    place = models.CharField(_('Place'), max_length=150, blank=True)
    post = models.CharField(_('Post Office'), max_length=150, blank=True)
    city = models.CharField(_('City'), max_length=150, blank=True)
    state = models.CharField(_('State'), max_length=150, blank=True)
    pin = models.CharField(_('PIN Code'), max_length=20, blank=True)
    photo = models.ImageField(_('Profile Photo'), upload_to='candidate_photos/', blank=True, null=True)
    resume = models.FileField(_('Resume PDF'), upload_to='candidate_resumes/', blank=True, null=True)
    qualifications = models.TextField(_('Qualifications'), blank=True)
    skills = models.TextField(_('Skills (comma-separated)'), blank=True)
    experience_years = models.DecimalField(_('Years of Experience'), max_digits=4, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Candidate Profile')
        verbose_name_plural = _('Candidate Profiles')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
