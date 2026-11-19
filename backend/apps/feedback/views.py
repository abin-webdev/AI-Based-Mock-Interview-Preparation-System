from rest_framework import generics, status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Feedback
from .serializers import FeedbackSerializer


@extend_schema(tags=['Feedback'])
class FeedbackListCreateView(generics.ListCreateAPIView):
    """
    List user's feedback or submit new system feedback.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'ADMIN':
            return Feedback.objects.all().order_by('-created_at')
        return Feedback.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
