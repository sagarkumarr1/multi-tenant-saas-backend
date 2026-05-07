from rest_framework.permissions import BasePermission
from users.models import User


class IsAdminOrManager(BasePermission):
    """Only Admin and Manager roles can access this view."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in [User.ADMIN, User.MANAGER]


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
    - Admin: full access to all users in same tenant
    - User: can only access their own profile
    - Manager: can only access users they created
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin has full access
        if request.user.role == User.ADMIN:
            return True

        # User can access their own profile
        if obj == request.user:
            return True

        # Manager can only access users they created
        if request.user.role == User.MANAGER and obj.created_by == request.user:
            return True

        return False
