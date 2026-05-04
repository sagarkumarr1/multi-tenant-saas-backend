from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import *
from .permissions import IsAdminOrManager, IsOwnerOrAdmin
from core.models import AuditLog

from rest_framework.pagination import PageNumberPagination

from .throttles import LoginRateThrottle


# 🔐 Login
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

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )


# 👤 Profile
class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        tenant_name = user.tenant.organization_name if user.tenant else "No Tenant"

        return Response({
            "message": f"Welcome {user.username}",
            "user": user.username,
            "tenant": tenant_name,
        })


# 🆕 Register (Admin + Manager only)
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


# 📋 User List (Tenant + Role based)
class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        user = request.user
        tenant = user.tenant

        # 🔐 Base queryset (RBAC + tenant + active)
        if user.role == User.ADMIN:
            users = User.objects.filter(tenant=tenant, is_active=True)

        elif user.role == User.MANAGER:
            users = User.objects.filter(
                created_by=user,
                tenant=tenant,
                is_active=True
            )

        else:
            return Response({"error": "Not allowed"}, status=403)

        # 🔍 Search (independent)
        search = request.query_params.get('search')
        if search:
            users = users.filter(username__icontains=search)

        # 🎯 Filter by role
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)

        # 🔃 Sorting
        ordering = request.query_params.get('ordering')
        allowed_fields = ['username', 'role', 'created_at']

        if ordering:
            field = ordering.replace('-', '')
            if field in allowed_fields:
                users = users.order_by(ordering)
        else:
            # default sorting (latest first)
            users = users.order_by('-created_at')

        # 📄 Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 5

        paginated_users = paginator.paginate_queryset(users, request)

        data = [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at
            }
            for u in paginated_users
        ]

        return paginator.get_paginated_response(data)
 


# 🔍 User Detail + Update + Delete
class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)

        return Response({
            "username": user.username,
            "role": user.role
        })

    def patch(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)

        user.username = request.data.get("username", user.username)
        user.save()

        return Response({"message": "User updated"})

    def delete(self, request, user_id):
        user = self.get_object(user_id)
        self.check_object_permissions(request, user)

        # ❌ Prevent self-delete
        if user == request.user:
            return Response(
                {"error": "You cannot delete yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🧾 Audit log
        AuditLog.objects.create(
            action="DELETE_USER",
            performed_by=request.user,
            target_user=user
        )

         # Soft delete
        user.is_active = False
        user.save()

        return Response({"message": "User deleted successfully"})
    

class RestoreUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # ❌ inactive user ही restore होगा
        if user.is_active:
            return Response(
                {"error": "User already active"},
                status=400
            )

        # 🔐 Permission logic
        if request.user.role == User.ADMIN:
            pass

        elif request.user.role == User.MANAGER:
            if user.created_by != request.user:
                return Response({"error": "Not allowed"}, status=403)

        else:
            return Response({"error": "Not allowed"}, status=403)

        # 🔄 Restore user
        user.is_active = True
        user.save()

        # 🧾 Audit log
        AuditLog.objects.create(
            action="RESTORE_USER",
            performed_by=request.user,
            target_user=user
        )

        return Response({"message": "User restored successfully"})
    

class ChangeUserRoleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # ❌ Only admin allowed
        if request.user.role != User.ADMIN:
            return Response({"error": "Only admin can change roles"}, status=403)

        # ❌ Prevent self role change
        if user == request.user:
            return Response({"error": "You cannot change your own role"}, status=400)

        new_role = request.data.get("role")

        # ❌ Validate role
        if new_role not in [User.ADMIN, User.MANAGER, User.USER_ROLE]:
            return Response({"error": "Invalid role"}, status=400)

        # ✅ Update role
        user.role = new_role
        user.save()

        # 🧾 Audit log
        AuditLog.objects.create(
            action=f"CHANGE_ROLE_TO_{new_role}",
            performed_by=request.user,
            target_user=user
        )

        return Response({"message": "User role updated successfully"})
    

class BulkDeleteUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = BulkUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        current_user = request.user

        users = User.objects.filter(id__in=user_ids)

        deleted_users = []

        for user in users:
            # ❌ self delete block
            if user == current_user:
                continue

            # 🔐 permission check
            if current_user.role == User.ADMIN:
                pass

            elif current_user.role == User.MANAGER:
                if user.created_by != current_user:
                    continue

            else:
                continue

            user.is_active = False
            user.save()

            # audit
            AuditLog.objects.create(
                action="BULK_DELETE_USER",
                performed_by=current_user,
                target_user=user
            )

            deleted_users.append(user.username)

        return Response({
            "deleted": deleted_users
        })
    
class BulkRestoreUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = BulkUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        current_user = request.user

        users = User.objects.filter(id__in=user_ids)

        restored_users = []

        for user in users:
            if user.is_active:
                continue

            # permission check
            if current_user.role == User.ADMIN:
                pass

            elif current_user.role == User.MANAGER:
                if user.created_by != current_user:
                    continue

            else:
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
            "restored": restored_users
        })
    
class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        user = request.user
        tenant = user.tenant

        # 🔐 tenant base filter
        users = User.objects.filter(tenant=tenant)

        # 📊 stats
        total_users = users.count()
        active_users = users.filter(is_active=True).count()
        inactive_users = users.filter(is_active=False).count()

        admin_count = users.filter(role=User.ADMIN).count()
        manager_count = users.filter(role=User.MANAGER).count()
        normal_users = users.filter(role=User.USER_ROLE).count()

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "roles": {
                "admins": admin_count,
                "managers": manager_count,
                "users": normal_users
            }
        })