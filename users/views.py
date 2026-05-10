from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination

from .models import User

# FIX #10 — Explicit imports instead of wildcard (from .serializers import *)
from .serializers import LoginSerializer, RegisterSerializer, BulkUserActionSerializer
from .permissions import IsAdminOrManager, IsOwnerOrAdmin
from .throttles import LoginRateThrottle
from core.models import AuditLog


# ─────────────────────────────────────────────
# LOGIN — Returns JWT access + refresh token
# ─────────────────────────────────────────────
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


# ─────────────────────────────────────────────
# PROFILE — View your own profile
# ─────────────────────────────────────────────
class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tenant_name = user.tenant.organization_name if user.tenant else "No Tenant"

        #Added 'role' to response
        return Response({
            "username": user.username,
            "role": user.role,
            "tenant": tenant_name,
        })


# ─────────────────────────────────────────────
# REGISTER — Create a new user (Admin/Manager only)
# ─────────────────────────────────────────────
class RegisterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────
# USER LIST — List all users (tenant-scoped)
# ─────────────────────────────────────────────
class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        user = request.user
        tenant = user.tenant

        if user.role == User.ADMIN:
            users = User.objects.filter(tenant=tenant, is_active=True).select_related('tenant')
        elif user.role == User.MANAGER:
            users = User.objects.filter(
                created_by=user, tenant=tenant, is_active=True
            ).select_related('tenant')
        else:
            return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        # Search by username
        search = request.query_params.get('search')
        if search:
            users = users.filter(username__icontains=search)

        # Filter by role
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)

        # Sorting — only allowed fields
        ordering = request.query_params.get('ordering')
        allowed_fields = ['username', 'role', 'created_at']
        if ordering:
            field = ordering.lstrip('-')
            if field in allowed_fields:
                users = users.order_by(ordering)
        else:
            users = users.order_by('-created_at')

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 5
        paginated_users = paginator.paginate_queryset(users, request)

        data = [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at,
            }
            for u in paginated_users
        ]

        return paginator.get_paginated_response(data)


# ─────────────────────────────────────────────
# USER DETAIL — Get / Update / Soft Delete
# ─────────────────────────────────────────────
class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)
        return Response({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
        })

    def patch(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)
 
        new_username = request.data.get("username", "").strip()

        if not new_username:
            return Response(
                {"error": "Username cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_username) > 150:
            return Response(
                {"error": "Username must be 150 characters or fewer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Duplicate username check
        if new_username != user.username and User.objects.filter(username=new_username).exists():
            return Response(
                {"error": "This username is already taken"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.username = new_username
        user.save()
        return Response({"message": "User updated successfully"})

    def delete(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)

        # Block self-delete
        if user == request.user:
            return Response(
                {"error": "You cannot delete yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is already deleted
        if not user.is_active:
            return Response(
                {"error": "User is already deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        AuditLog.objects.create(
            action="DELETE_USER",
            performed_by=request.user,
            target_user=user
        )

        user.is_active = False
        user.save()
        return Response({"message": "User deleted successfully"})


# ─────────────────────────────────────────────
# RESTORE — Bring back a soft-deleted user
# ─────────────────────────────────────────────
class RestoreUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request, user_id):
        # FIX #6 — Tenant isolation added: fetch user scoped to current user's tenant
        user = get_object_or_404(User, id=user_id, tenant=request.user.tenant)

        if user.is_active:
            return Response(
                {"error": "User is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.role == User.MANAGER and user.created_by != request.user:
            return Response(
                {"error": "You can only restore users you created"},
                status=status.HTTP_403_FORBIDDEN
            )

        user.is_active = True
        user.save()

        AuditLog.objects.create(
            action="RESTORE_USER",
            performed_by=request.user,
            target_user=user
        )
        return Response({"message": "User restored successfully"})


# ─────────────────────────────────────────────
# CHANGE ROLE — Change a user's role (Admin only)
# ─────────────────────────────────────────────
class ChangeUserRoleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if request.user.role != User.ADMIN:
            return Response(
                {"error": "Only admins can change roles"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Tenant isolation added: Admin cannot change roles of other tenants
        user = get_object_or_404(User, id=user_id, tenant=request.user.tenant)

        if user == request.user:
            return Response(
                {"error": "You cannot change your own role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_role = request.data.get("role")
        valid_roles = [User.ADMIN, User.MANAGER, User.USER_ROLE]
        if new_role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Choose from: {valid_roles}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.role = new_role
        user.save()

        AuditLog.objects.create(
            action=f"CHANGE_ROLE_TO_{new_role}",
            performed_by=request.user,
            target_user=user
        )
        return Response({"message": f"User role changed to {new_role} successfully"})


# ─────────────────────────────────────────────
# BULK DELETE — Soft delete multiple users at once
# ─────────────────────────────────────────────
class BulkDeleteUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = BulkUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        current_user = request.user

        users = User.objects.filter(id__in=user_ids, tenant=current_user.tenant)

        deleted_users = []
        skipped_users = []

        for user in users:
            # Cannot delete yourself
            if user == current_user:
                skipped_users.append({"username": user.username, "reason": "Cannot delete yourself"})
                continue

            # Manager can only delete users they created
            if current_user.role == User.MANAGER and user.created_by != current_user:
                skipped_users.append({"username": user.username, "reason": "Not your user"})
                continue

            # Skip already-deleted users
            if not user.is_active:
                skipped_users.append({"username": user.username, "reason": "Already deleted"})
                continue

            user.is_active = False
            user.save()

            AuditLog.objects.create(
                action="BULK_DELETE_USER",
                performed_by=current_user,
                target_user=user
            )
            deleted_users.append(user.username)

        return Response({
            "deleted": deleted_users,
            "skipped": skipped_users,
        })


# ─────────────────────────────────────────────
# BULK RESTORE — Restore multiple users at once
# ─────────────────────────────────────────────
class BulkRestoreUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = BulkUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        current_user = request.user

        users = User.objects.filter(id__in=user_ids, tenant=current_user.tenant)

        restored_users = []
        skipped_users = []

        for user in users:
            # Skip already-active users
            if user.is_active:
                skipped_users.append({"username": user.username, "reason": "Already active"})
                continue

            # Manager can only restore users they created
            if current_user.role == User.MANAGER and user.created_by != current_user:
                skipped_users.append({"username": user.username, "reason": "Not your user"})
                continue

            user.is_active = True
            user.save()

            AuditLog.objects.create(
                action="BULK_RESTORE_USER",
                performed_by=current_user,
                target_user=user
            )
            restored_users.append(user.username)

        return Response({
            "restored": restored_users,
            "skipped": skipped_users,
        })


# ─────────────────────────────────────────────
# DASHBOARD — Tenant stats overview
# ─────────────────────────────────────────────
class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        tenant = request.user.tenant
        users = User.objects.filter(tenant=tenant)

        return Response({
            "total_users": users.count(),
            "active_users": users.filter(is_active=True).count(),
            "inactive_users": users.filter(is_active=False).count(),
            "roles": {
                "admins": users.filter(role=User.ADMIN).count(),
                "managers": users.filter(role=User.MANAGER).count(),
                "users": users.filter(role=User.USER_ROLE).count(),
            }
        })


# ─────────────────────────────────────────────
# LOGOUT — Refresh token blacklist 
# ─────────────────────────────────────────────
class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .serializers import LogoutSerializer
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Refresh token ko blacklist karo — ab ye token kaam nahi karega
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            return Response(
                {"message": "Logged out successfully. Token has been blacklisted."},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"error": "Invalid or already blacklisted token."},
                status=status.HTTP_400_BAD_REQUEST
            )
