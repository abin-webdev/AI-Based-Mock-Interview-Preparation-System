from rest_framework import serializers
from .models import CandidateProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class CandidateProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'dob',
            'gender', 'place', 'post', 'city', 'state', 'pin',
            'photo', 'resume', 'qualifications', 'skills',
            'experience_years', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']


class CandidateProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = [
            'full_name', 'phone', 'dob', 'gender', 'place', 'post',
            'city', 'state', 'pin', 'qualifications', 'skills', 'experience_years'
        ]


class CandidatePhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ['photo']

    def validate_photo(self, value):
        if value:
            # Max 5MB for photo
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Profile photo cannot exceed 5MB.")
            # Verify file extension
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise serializers.ValidationError("Only JPG, JPEG, PNG, or WEBP images are supported.")
        return value


class CandidateResumeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ['resume']

    def validate_resume(self, value):
        if value:
            # Max 15MB for resume
            if value.size > 15 * 1024 * 1024:
                raise serializers.ValidationError("Resume document cannot exceed 15MB.")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise serializers.ValidationError("Only PDF, DOC, or DOCX files are allowed.")
        return value
