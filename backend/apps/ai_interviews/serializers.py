from rest_framework import serializers
from .models import AIMockSession, AIMockQuestion, AIMockAnswer, CameraTelemetryReport
from apps.candidates.models import CandidateProfile


class AIMockAnswerSerializer(serializers.ModelSerializer):
    question_number = serializers.IntegerField(source='question.question_number', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = AIMockAnswer
        fields = [
            'id',
            'session',
            'question',
            'question_number',
            'question_text',
            'answer_text',
            'time_taken_seconds',
            'submitted_at',
            'relevance_score',
            'accuracy_score',
            'completeness_score',
            'clarity_score',
            'overall_question_score',
            'feedback',
            'strengths',
            'improvement_areas',
        ]
        read_only_fields = [
            'id', 'session', 'submitted_at', 'relevance_score',
            'accuracy_score', 'completeness_score', 'clarity_score',
            'overall_question_score', 'feedback', 'strengths', 'improvement_areas'
        ]


class AIMockQuestionSerializer(serializers.ModelSerializer):
    has_answer = serializers.SerializerMethodField()
    answer = AIMockAnswerSerializer(read_only=True)

    class Meta:
        model = AIMockQuestion
        fields = [
            'id',
            'session_id',
            'question_number',
            'question_text',
            'category',
            'expected_keywords',
            'evaluation_rubric',
            'has_answer',
            'answer',
            'created_at',
        ]
        read_only_fields = ['id', 'session_id', 'created_at']

    def get_has_answer(self, obj):
        return hasattr(obj, 'answer') and obj.answer is not None


class AIMockSessionSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    questions = AIMockQuestionSerializer(many=True, read_only=True)
    total_answered = serializers.SerializerMethodField()

    class Meta:
        model = AIMockSession
        fields = [
            'id',
            'candidate',
            'candidate_name',
            'job_role',
            'category',
            'difficulty',
            'question_count',
            'duration_minutes',
            'status',
            'camera_consent_given',
            'overall_score',
            'summary_feedback',
            'strengths_summary',
            'improvements_summary',
            'started_at',
            'completed_at',
            'total_answered',
            'questions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'candidate', 'candidate_name', 'status', 'overall_score',
            'summary_feedback', 'strengths_summary', 'improvements_summary',
            'started_at', 'completed_at', 'total_answered', 'questions',
            'created_at', 'updated_at'
        ]

    def get_total_answered(self, obj):
        return obj.answers.count()


class CreateAIMockSessionSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(default=5, min_value=1, max_value=20)
    duration_minutes = serializers.IntegerField(default=15, min_value=5, max_value=60)
    camera_consent_given = serializers.BooleanField(default=False)

    class Meta:
        model = AIMockSession
        fields = [
            'job_role',
            'category',
            'difficulty',
            'question_count',
            'duration_minutes',
            'camera_consent_given',
        ]


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    answer_text = serializers.CharField(required=True, min_length=3)
    time_taken_seconds = serializers.IntegerField(required=False, default=0, min_value=0)


class CameraTelemetryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraTelemetryReport
        fields = [
            'id',
            'session_id',
            'consent_given',
            'frames_processed',
            'centered_posture_percentage',
            'head_stability_score',
            'eye_contact_ratio',
            'observations',
            'disclaimer',
            'created_at',
        ]
        read_only_fields = ['id', 'session_id', 'disclaimer', 'created_at']


class UploadCameraTelemetrySerializer(serializers.Serializer):
    consent_given = serializers.BooleanField(required=False, default=True)
    frames_processed = serializers.IntegerField(required=False, default=1, min_value=1)
    centered_posture_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=85.0)
    head_stability_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=80.0)
    eye_contact_ratio = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=82.0)
    frame_image = serializers.ImageField(required=False, allow_null=True)


class AIMockInterviewResultsSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)
    questions = AIMockQuestionSerializer(many=True, read_only=True)
    camera_telemetry = CameraTelemetryReportSerializer(read_only=True)
    total_questions = serializers.SerializerMethodField()
    total_answered = serializers.SerializerMethodField()

    class Meta:
        model = AIMockSession
        fields = [
            'id',
            'candidate_id',
            'candidate_name',
            'candidate_email',
            'job_role',
            'category',
            'difficulty',
            'status',
            'overall_score',
            'summary_feedback',
            'strengths_summary',
            'improvements_summary',
            'duration_minutes',
            'started_at',
            'completed_at',
            'total_questions',
            'total_answered',
            'questions',
            'camera_telemetry',
            'created_at',
        ]
        read_only_fields = fields

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_total_answered(self, obj):
        return obj.answers.count()

