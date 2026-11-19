from rest_framework import serializers
from apps.vacancies.models import Vacancy
from apps.companies.models import CompanyProfile


class PublicCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ['id', 'company_name', 'email', 'phone', 'website', 'address', 'logo']


class VacancyListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'company_id', 'company_name', 'company_logo',
            'position', 'location', 'experience_years', 'salary_range',
            'no_of_vacancy', 'start_date', 'application_deadline',
            'status', 'is_expired', 'created_at'
        ]


class VacancyDetailSerializer(serializers.ModelSerializer):
    company = PublicCompanySerializer(read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'company', 'position', 'description',
            'required_qualifications', 'required_skills',
            'experience_years', 'location', 'salary_range',
            'no_of_vacancy', 'start_date', 'application_deadline',
            'status', 'is_expired', 'created_at', 'updated_at'
        ]


class VacancyApplySerializer(serializers.Serializer):
    resume = serializers.FileField(required=False, allow_null=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True)
