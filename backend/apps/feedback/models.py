from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_('User')
    )
    feedback_text = models.TextField(_('Feedback'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('User Feedback')
        verbose_name_plural = _('User Feedbacks')
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback #{self.id} from {self.user.email}"
