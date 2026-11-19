from rest_framework import permissions
from .models import User


class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with the ADMIN role or superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.ADMIN or request.user.is_superuser)
        )


class IsCompanyRole(permissions.BasePermission):
    """
    Allows access only to authenticated users with the COMPANY role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.COMPANY
        )


class IsCandidateRole(permissions.BasePermission):
    """
    Allows access only to authenticated users with the CANDIDATE role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.CANDIDATE
        )


class IsVerifiedCompany(permissions.BasePermission):
    """
    Allows access only to companies that have been verified and approved by admin.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == User.Role.COMPANY):
            return False
        profile = getattr(request.user, 'company_profile', None)
        return bool(profile and profile.verification_status == 'APPROVED')


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission allowing only the owner or an admin to view/modify the record.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_admin_role:
            return True
        # Check standard user relations
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'candidate') and hasattr(obj.candidate, 'user'):
            return obj.candidate.user == request.user
        if hasattr(obj, 'company') and hasattr(obj.company, 'user'):
            return obj.company.user == request.user
        return False
