from rest_framework import generics, status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Complaint
from .serializers import ComplaintSerializer, CreateComplaintSerializer


@extend_schema(tags=['Complaints'])
class ComplaintListCreateView(generics.ListCreateAPIView):
    """
    List user's filed complaints or file a new complaint against a company / platform.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateComplaintSerializer
        return ComplaintSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'ADMIN':
            return Complaint.objects.all().order_by('-created_at')
        return Complaint.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=['Complaints'])
class ComplaintDetailView(generics.RetrieveAPIView):
    """
    Retrieve single complaint details and admin reply history.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'ADMIN':
            return Complaint.objects.all()
        return Complaint.objects.filter(user=user)
