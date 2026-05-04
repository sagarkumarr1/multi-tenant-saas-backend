from rest_framework import permissions
from rest_framework.permissions import BasePermission
from users.models import User
class IsAdminUserCustom(permissions.BasePermission):
  def has_permission(self, request, view):
        # 1. Check karo user logged in hai ya nahi
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 2. Check karo user ka role 'ADMIN' hai ya nahi
        return request.user.role == User.ADMIN
  

class IsAdminOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # role check
        return request.user.role in [User.ADMIN, User.MANAGER]
    


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        # authenticated check
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin → full access
        if request.user.role == User.ADMIN:
            return True

        # Owner → self profile
        if obj == request.user:
            return True

        # Manager → only users created by them
        if request.user.role == User.MANAGER and obj.created_by == request.user:
            return True

        return False