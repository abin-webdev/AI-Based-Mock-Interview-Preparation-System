from rest_framework import serializers
from .models import TestSchedule, TestCandidateAssignment
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy


class TestCandidateAssignmentSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone', read_only=True)

    class Meta:
        model = TestCandidateAssignment
        fields = [
            'id', 'candidate_id', 'candidate_name', 'candidate_email',
            'candidate_phone', 'attendance_status', 'score', 'remarks', 'assigned_at'
        ]
        read_only_fields = ['id', 'candidate_id', 'candidate_name', 'candidate_email', 'candidate_phone', 'assigned_at']


class TestScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    vacancy_position = serializers.CharField(source='vacancy.position', read_only=True)
    candidate_assignments = TestCandidateAssignmentSerializer(many=True, read_only=True)
    assigned_count = serializers.SerializerMethodField()

    class Meta:
        model = TestSchedule
        fields = [
            'id', 'company_id', 'company_name', 'vacancy_id', 'vacancy_position',
            'test_name', 'test_type', 'date', 'start_time', 'end_time',
            'duration_minutes', 'total_marks', 'pass_marks', 'instructions',
            'status', 'assigned_count', 'candidate_assignments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company_id', 'company_name', 'assigned_count', 'created_at', 'updated_at']

    def get_assigned_count(self, obj):
        return obj.candidate_assignments.count()

    def validate(self, attrs):
        start = attrs.get('start_time') or (self.instance.start_time if self.instance else None)
        end = attrs.get('end_time') or (self.instance.end_time if self.instance else None)
        if start and end and start >= end:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs


class AssignCandidatesSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True
    )


class RecordAttendanceSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField(required=True)
    attendance_status = serializers.ChoiceField(
        choices=TestCandidateAssignment.Attendance.choices,
        required=True
    )
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
