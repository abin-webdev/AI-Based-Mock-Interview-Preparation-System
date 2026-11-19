from rest_framework import serializers
from .models import CompanyProfile, CompanyReview
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from apps.candidates.models import CandidateProfile


class CompanyProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'user_email', 'company_name', 'email', 'phone', 'address',
            'website', 'description', 'logo', 'registration_document',
            'verification_status', 'rejection_reason', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'verification_status', 'rejection_reason', 'created_at', 'updated_at']


class CompanyProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'phone', 'address', 'website', 'description', 'logo']


class CompanyVacancySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [
            'id', 'company_id', 'company_name', 'position', 'description',
            'required_qualifications', 'required_skills', 'experience_years',
            'location', 'salary_range', 'no_of_vacancy', 'start_date',
            'application_deadline', 'status', 'is_expired', 'applications_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company_id', 'company_name', 'is_expired', 'applications_count', 'created_at', 'updated_at']

    def get_applications_count(self, obj):
        return obj.applications.count()


class CandidateSummaryForCompanySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'full_name', 'email', 'phone', 'city', 'state',
            'qualifications', 'skills', 'experience_years', 'photo', 'resume'
        ]


class CompanyApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateSummaryForCompanySerializer(read_only=True)
    vacancy_position = serializers.CharField(source='vacancy.position', read_only=True)
    vacancy_id = serializers.IntegerField(source='vacancy.id', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'vacancy_id', 'vacancy_position', 'candidate',
            'resume', 'cover_letter', 'status', 'company_notes',
            'applied_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vacancy_id', 'vacancy_position', 'candidate', 'resume', 'cover_letter', 'applied_at', 'updated_at']


class CompanyApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices, required=True)
    company_notes = serializers.CharField(required=False, allow_blank=True)


class CompanyReviewSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)

    class Meta:
        model = CompanyReview
        fields = ['id', 'company_id', 'candidate_name', 'rating', 'review', 'created_at']
        read_only_fields = ['id', 'company_id', 'candidate_name', 'created_at']
