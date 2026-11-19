from rest_framework import serializers
from apps.companies.models import CompanyProfile
from apps.candidates.models import CandidateProfile
from apps.applications.models import Application
from .models import InterviewSchedule
from .services import validate_scheduling_conflict


class InterviewScheduleSerializer(serializers.ModelSerializer):
    candidate_id = serializers.PrimaryKeyRelatedField(
        queryset=CandidateProfile.objects.all(),
        source='candidate',
        write_only=True
    )
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        source='application',
        write_only=True,
        required=False,
        allow_null=True
    )
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone', read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = [
            'id',
            'company',
            'company_name',
            'candidate_id',
            'candidate',
            'candidate_name',
            'candidate_email',
            'candidate_phone',
            'application_id',
            'application',
            'interview_title',
            'interview_type',
            'date',
            'start_time',
            'end_time',
            'meeting_link',
            'location',
            'status',
            'cancellation_reason',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'company', 'candidate', 'application', 'status', 'cancellation_reason', 'created_at', 'updated_at']

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        date = attrs.get('date')
        candidate = attrs.get('candidate')
        request = self.context.get('request')

        if request and hasattr(request.user, 'company_profile'):
            company = request.user.company_profile
            has_conflict, message = validate_scheduling_conflict(
                candidate=candidate,
                company=company,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            if has_conflict:
                raise serializers.ValidationError({'scheduling_conflict': message})

        return attrs


class InterviewRescheduleSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    end_time = serializers.TimeField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        date = attrs.get('date')
        interview = self.context.get('interview')

        if start_time >= end_time:
            raise serializers.ValidationError({'start_time': 'Start time must be before end time.'})

        if interview:
            has_conflict, message = validate_scheduling_conflict(
                candidate=interview.candidate,
                company=interview.company,
                date=date,
                start_time=start_time,
                end_time=end_time,
                exclude_interview_id=interview.id
            )
            if has_conflict:
                raise serializers.ValidationError({'scheduling_conflict': message})

        return attrs


class InterviewCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=True, min_length=3)
