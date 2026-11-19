from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.complaints.models import Complaint
from apps.feedback.models import Feedback
from apps.vacancies.models import Vacancy
from apps.ai_interviews.models import AIMockSession

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    profile_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'created_at', 'last_login', 'profile_name']

    def get_profile_name(self, obj):
        if obj.role == User.Role.COMPANY and hasattr(obj, 'company_profile'):
            return obj.company_profile.company_name
        elif obj.role == User.Role.CANDIDATE and hasattr(obj, 'candidate_profile'):
            return obj.candidate_profile.full_name
        return obj.username


class AdminCompanyListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'user_id', 'company_name', 'email', 'phone', 'website',
            'verification_status', 'is_verified', 'is_active', 'created_at'
        ]


class AdminCompanyDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    verified_by_email = serializers.EmailField(source='verified_by.email', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'user_id', 'company_name', 'email', 'phone', 'address',
            'website', 'description', 'logo', 'registration_document',
            'verification_status', 'rejection_reason', 'verified_by_email',
            'verified_at', 'is_active', 'created_at', 'updated_at'
        ]


class AdminCompanyVerifySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=CompanyProfile.VerificationStatus.choices,
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)


class AdminComplaintSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    replied_by_email = serializers.EmailField(source='replied_by.email', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'user_id', 'user_email', 'company_id', 'company_name',
            'complaint_text', 'status', 'reply', 'replied_by_email',
            'replied_at', 'created_at', 'updated_at'
        ]


class AdminComplaintReplySerializer(serializers.Serializer):
    reply = serializers.CharField(required=True)
    status = serializers.ChoiceField(
        choices=Complaint.Status.choices,
        default=Complaint.Status.RESOLVED
    )


class AdminFeedbackSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'user_id', 'user_email', 'feedback_text', 'created_at']


class AdminVacancyListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'company_id', 'company_name', 'position', 'location',
            'no_of_vacancy', 'start_date', 'application_deadline',
            'status', 'is_expired', 'created_at'
        ]


class AdminInterviewMonitorSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)

    class Meta:
        model = AIMockSession
        fields = [
            'id', 'candidate_name', 'candidate_email', 'job_role',
            'category', 'difficulty', 'question_count', 'duration_minutes',
            'status', 'started_at', 'completed_at', 'created_at'
        ]
