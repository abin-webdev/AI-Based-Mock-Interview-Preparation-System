from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.candidates.models import CandidateProfile


class AIMockSession(models.Model):
    class Category(models.TextChoices):
        TECHNICAL = 'TECHNICAL', _('Technical Round')
        HR = 'HR', _('HR Round')
        GENERAL = 'GENERAL', _('General & Behavioral Round')
        JOB_SPECIFIC = 'JOB_SPECIFIC', _('Job-Specific Competencies')

    class Difficulty(models.TextChoices):
        JUNIOR = 'JUNIOR', _('Junior / Entry Level')
        MID = 'MID', _('Mid-Level')
        SENIOR = 'SENIOR', _('Senior / Lead Level')

    class Status(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        ABANDONED = 'ABANDONED', _('Abandoned')

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='ai_mock_sessions',
        verbose_name=_('Candidate')
    )
    job_role = models.CharField(_('Target Job Role'), max_length=255)
    category = models.CharField(
        _('Interview Category'),
        max_length=30,
        choices=Category.choices,
        default=Category.TECHNICAL
    )
    difficulty = models.CharField(
        _('Difficulty Level'),
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.JUNIOR
    )
    question_count = models.PositiveIntegerField(_('Number of Questions'), default=5)
    duration_minutes = models.PositiveIntegerField(_('Allocated Duration (Minutes)'), default=15)
    status = models.CharField(
        _('Session Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True
    )
    camera_consent_given = models.BooleanField(_('Camera Consent Given'), default=False)
    overall_score = models.DecimalField(_('Overall Performance Score'), max_digits=5, decimal_places=2, null=True, blank=True)
    summary_feedback = models.TextField(_('Summary Feedback'), blank=True)
    strengths_summary = models.TextField(_('Strengths Summary'), blank=True)
    improvements_summary = models.TextField(_('Improvements Summary'), blank=True)
    started_at = models.DateTimeField(_('Session Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Session Completed At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('AI Mock Session')
        verbose_name_plural = _('AI Mock Sessions')
        ordering = ['-created_at']

    def __str__(self):
        return f"AI Mock Session #{self.id} - {self.job_role} ({self.candidate.full_name})"


class AIMockQuestion(models.Model):
    session = models.ForeignKey(
        AIMockSession,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Mock Session')
    )
    question_number = models.PositiveIntegerField(_('Question Number'))
    question_text = models.TextField(_('Question Text'))
    category = models.CharField(_('Category'), max_length=50, blank=True)
    expected_keywords = models.TextField(_('Expected Key Concepts (comma-separated)'), blank=True)
    evaluation_rubric = models.TextField(_('Evaluation Rubric / Key Answers'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('AI Mock Question')
        verbose_name_plural = _('AI Mock Questions')
        ordering = ['session', 'question_number']
        unique_together = ('session', 'question_number')

    def __str__(self):
        return f"Q{self.question_number} for Session #{self.session_id}: {self.question_text[:50]}"


class AIMockAnswer(models.Model):
    session = models.ForeignKey(
        AIMockSession,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Mock Session')
    )
    question = models.OneToOneField(
        AIMockQuestion,
        on_delete=models.CASCADE,
        related_name='answer',
        verbose_name=_('Question')
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='mock_answers',
        verbose_name=_('Candidate')
    )
    answer_text = models.TextField(_('Candidate Answer'))
    time_taken_seconds = models.PositiveIntegerField(_('Time Taken (Seconds)'), default=0)
    submitted_at = models.DateTimeField(_('Submitted At'), auto_now_add=True)

    # Evaluation breakdown (populated via NLP/LLM in Phase 10)
    relevance_score = models.DecimalField(_('Relevance Score (0-10)'), max_digits=4, decimal_places=1, null=True, blank=True)
    accuracy_score = models.DecimalField(_('Technical Accuracy Score (0-10)'), max_digits=4, decimal_places=1, null=True, blank=True)
    completeness_score = models.DecimalField(_('Completeness Score (0-10)'), max_digits=4, decimal_places=1, null=True, blank=True)
    clarity_score = models.DecimalField(_('Clarity & Communication (0-10)'), max_digits=4, decimal_places=1, null=True, blank=True)
    overall_question_score = models.DecimalField(_('Overall Score (0-100)'), max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(_('Evaluation Feedback'), blank=True)
    strengths = models.TextField(_('Strengths Observed'), blank=True)
    improvement_areas = models.TextField(_('Key Areas for Improvement'), blank=True)

    class Meta:
        verbose_name = _('AI Mock Answer')
        verbose_name_plural = _('AI Mock Answers')
        ordering = ['submitted_at']

    def __str__(self):
        return f"Answer to Q{self.question.question_number} (Session #{self.session_id})"


class CameraTelemetryReport(models.Model):
    session = models.OneToOneField(
        AIMockSession,
        on_delete=models.CASCADE,
        related_name='camera_telemetry',
        verbose_name=_('Mock Session')
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='camera_telemetry_reports',
        verbose_name=_('Candidate')
    )
    consent_given = models.BooleanField(_('Candidate Explicit Consent Given'), default=True)
    frames_processed = models.PositiveIntegerField(_('Number of Frames Processed'), default=0)
    centered_posture_percentage = models.DecimalField(
        _('Centered Posture Ratio (%)'),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_('Percentage of frames where candidate remained centrally aligned in camera view.')
    )
    head_stability_score = models.DecimalField(
        _('Head Posture Stability Score (0-100)'),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_('Observational measure of steady upright framing without erratic shifts.')
    )
    eye_contact_ratio = models.DecimalField(
        _('Camera Focus / Eye Alignment Ratio (%)'),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text=_('Percentage of time facing towards screen / camera.')
    )
    observations = models.TextField(_('Telemetry Observations'), blank=True)
    disclaimer = models.TextField(
        _('Ethical & Privacy Disclaimer'),
        default="Advisory behavioral telemetry only. Does NOT assess personality, emotion, or psychological traits. Must never be used as an automatic hiring or rejection criterion."
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Camera Telemetry Report')
        verbose_name_plural = _('Camera Telemetry Reports')

    def __str__(self):
        return f"Camera Telemetry for Session #{self.session_id} ({self.candidate.full_name})"
