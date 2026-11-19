from rest_framework import serializers
from apps.applications.models import Application
from apps.vacancies.serializers import VacancyListSerializer


class CandidateApplicationListSerializer(serializers.ModelSerializer):
    vacancy_position = serializers.CharField(source='vacancy.position', read_only=True)
    company_name = serializers.CharField(source='vacancy.company.company_name', read_only=True)
    company_logo = serializers.ImageField(source='vacancy.company.logo', read_only=True)
    location = serializers.CharField(source='vacancy.location', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'vacancy_id', 'vacancy_position', 'company_name', 'company_logo',
            'location', 'status', 'applied_at', 'updated_at'
        ]


class CandidateApplicationDetailSerializer(serializers.ModelSerializer):
    vacancy = VacancyListSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'vacancy', 'status', 'resume', 'cover_letter',
            'applied_at', 'updated_at'
        ]
