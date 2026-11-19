from rest_framework import serializers
from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['id', 'user', 'user_email', 'user_name', 'feedback_text', 'created_at']
        read_only_fields = ['id', 'user', 'user_email', 'user_name', 'created_at']

    def get_user_name(self, obj):
        if hasattr(obj.user, 'candidate_profile'):
            return obj.user.candidate_profile.full_name
        elif hasattr(obj.user, 'company_profile'):
            return obj.user.company_profile.company_name
        return obj.user.username
