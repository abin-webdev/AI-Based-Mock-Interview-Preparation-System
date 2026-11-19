from rest_framework import serializers
from .models import Complaint
from apps.companies.models import CompanyProfile


class ComplaintSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    replied_by_name = serializers.CharField(source='replied_by.username', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'user',
            'user_email',
            'company',
            'company_name',
            'complaint_text',
            'status',
            'reply',
            'replied_by',
            'replied_by_name',
            'replied_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'user_email', 'status', 'reply', 'replied_by', 'replied_at', 'created_at', 'updated_at']


class CreateComplaintSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyProfile.objects.all(),
        source='company',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Complaint
        fields = ['id', 'company_id', 'complaint_text', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
