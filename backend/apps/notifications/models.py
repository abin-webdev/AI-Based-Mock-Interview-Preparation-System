from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPLICATION = 'APPLICATION', _('Application Update')
        TEST = 'TEST', _('Test / Assessment')
        INTERVIEW = 'INTERVIEW', _('Interview Schedule')
        COMPLAINT = 'COMPLAINT', _('Complaint Reply')
        SYSTEM = 'SYSTEM', _('System Announcement')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User')
    )
    title = models.CharField(_('Notification Title'), max_length=255)
    message = models.TextField(_('Message Content'))
    notification_type = models.CharField(
        _('Notification Type'),
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    is_read = models.BooleanField(_('Is Read'), default=False, db_index=True)
    related_id = models.CharField(_('Related Entity ID'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title} (Read: {self.is_read})"
